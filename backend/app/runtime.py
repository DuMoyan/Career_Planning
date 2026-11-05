import asyncio
from contextlib import asynccontextmanager
from contextvars import ContextVar
from datetime import UTC, date, datetime
from uuid import NAMESPACE_URL, uuid5

from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_scoped_session

from app.agents.openai_compatible import build_planning_model
from app.agents.planning_graph import PlanningGraph
from app.core.database import create_engine, create_session_factory
from app.core.security import hash_password
from app.domain.access import Role
from app.domain.competency import calculate_profile
from app.domain.gap import analyze_gap
from app.models.assessment import AssessmentItemModel, AssessmentScaleModel
from app.models.goal import CareerGoal
from app.models.target import CareerTarget, CareerTargetRequirement
from app.repositories.ai_runs import SqlAlchemyAIRunRepository
from app.repositories.assessments import SqlAlchemyAssessmentRepository
from app.repositories.audits import SqlAlchemyAuditRepository
from app.repositories.competencies import SqlAlchemyCompetencyRepository
from app.repositories.grants import RedisGrantCache, SqlAlchemyGrantRepository
from app.repositories.mentor_comments import SqlAlchemyMentorCommentRepository
from app.repositories.plans import SqlAlchemyPlanRepository
from app.repositories.profiles import SqlAlchemyProfileRepository
from app.repositories.reports import SqlAlchemyReportRepository
from app.repositories.targets import SqlAlchemyTargetRepository
from app.repositories.tasks import SqlAlchemyTaskRepository
from app.repositories.users import SqlAlchemyUserRepository, UserRecord
from app.schemas.planning import PlanningContext, PlanningGap
from app.seed.assessments import build_demo_scales
from app.seed.targets import build_demo_targets
from app.services.admin import AdminService
from app.services.ai_runs import AIRunService
from app.services.assessments import AssessmentService
from app.services.auth import AuthService
from app.services.competencies import CompetencyService
from app.services.grants import GrantService
from app.services.mentor import MentorService
from app.services.plans import PlanService
from app.services.profiles import ProfileService
from app.services.reports import ReportService
from app.services.resumes import DiskFileStore, ResumeParser, ResumeService
from app.services.targets import GoalService, TargetService
from app.services.tasks import TaskService


async def configure_persistent_services(app, settings) -> None:
    engine = create_engine(settings.database_url)
    session_factory = create_session_factory(engine)
    request_scope: ContextVar[object | None] = ContextVar("database_request_scope", default=None)

    def session_scope():
        return request_scope.get() or asyncio.current_task()

    sessions = async_scoped_session(session_factory, scopefunc=session_scope)
    app.state.engine = engine
    app.state.db_sessions = sessions
    app.state.db_request_scope = request_scope

    await _seed_demo_data(session_factory)
    audits = SqlAlchemyAuditRepository(sessions)
    users = SqlAlchemyUserRepository(sessions)
    app.state.auth_service = AuthService(users=users, audits=audits, settings=settings)
    profiles = SqlAlchemyProfileRepository(sessions)
    app.state.profile_service = ProfileService(profiles)
    grant_repo = SqlAlchemyGrantRepository(sessions)
    redis = Redis.from_url(settings.redis_url, decode_responses=True)
    app.state.redis = redis
    app.state.grant_service = GrantService(
        repository=grant_repo,
        cache=RedisGrantCache(redis),
        audits=audits,
    )

    app.state.assessment_service = AssessmentService(SqlAlchemyAssessmentRepository(sessions))
    competencies = SqlAlchemyCompetencyRepository(sessions)
    app.state.competency_service = CompetencyService(competencies)
    app.state.resume_service = ResumeService(
        repository=competencies,
        files=DiskFileStore(settings.upload_dir),
        parser=ResumeParser(),
        max_bytes=settings.upload_max_bytes,
    )
    targets = SqlAlchemyTargetRepository(sessions)
    app.state.target_service = TargetService(targets, competencies)
    app.state.goal_service = GoalService(targets)
    plans = SqlAlchemyPlanRepository(sessions)
    tasks = SqlAlchemyTaskRepository(sessions)
    app.state.plan_service = PlanService(plans, tasks)
    app.state.task_service = TaskService(tasks, plans)
    async def planning_context(student_id):
        goals = await targets.list_goals(student_id)
        goal = next((item for item in goals if item.primary), None)
        if goal is None:
            raise RuntimeError("生成规划前必须先设置主目标")
        target = await targets.get_target(goal.target_id)
        if target is None:
            raise RuntimeError("主目标岗位不存在")
        evidence = await competencies.list_evidence(student_id)
        snapshot = calculate_profile([item.to_domain() for item in evidence])
        competency_profile = await competencies.latest_profile(student_id)
        student_profile = await profiles.get(student_id)
        profile = {
            code: (dimension.level, dimension.evidence_ids)
            for code, dimension in snapshot.dimensions.items()
        }
        gaps = analyze_gap(list(target.requirements), profile)
        references = {
            "goal_id": str(goal.id),
            "target_id": str(target.id),
            "target_verified_at": target.verified_at.isoformat(),
        }
        if competency_profile is not None:
            references["competency_profile_version"] = str(competency_profile.version)
        constraints = []
        if goal.constraints:
            constraints.append(goal.constraints)
        if student_profile is not None:
            constraints.extend(
                f"{key}: {value}" for key, value in student_profile.constraints.items()
            )
        return PlanningContext(
            goal_deadline=goal.deadline,
            weekly_hours=(
                goal.weekly_hours
                or (student_profile.available_hours if student_profile else 0)
                or 5
            ),
            gaps=[
                PlanningGap(
                    competency_code=item.competency_code,
                    status=item.status.value,
                    required_level=item.required_level,
                    current_level=item.current_level,
                    source=item.requirement_source,
                )
                for item in gaps
            ],
            input_references=references,
            preferences={"constraints": constraints} if constraints else {},
        )

    app.state.ai_run_service = AIRunService(
        repository=SqlAlchemyAIRunRepository(sessions),
        graph=PlanningGraph(build_planning_model(settings)),
        context_provider=planning_context,
        audits=audits,
        auto_process=False,
    )
    app.state.ai_run_tasks = set()

    async def process_ai_run(run_id, student_id):
        token = request_scope.set(object())
        try:
            await app.state.ai_run_service.process(run_id, student_id)
        finally:
            await sessions.remove()
            request_scope.reset(token)

    def schedule_ai_run(run_id, student_id):
        task = asyncio.create_task(process_ai_run(run_id, student_id))
        app.state.ai_run_tasks.add(task)
        task.add_done_callback(app.state.ai_run_tasks.discard)

    app.state.schedule_ai_run = schedule_ai_run

    async def start_replan(student_id, feedback):
        run = await app.state.ai_run_service.create(student_id, feedback=feedback)
        schedule_ai_run(run.id, student_id)
        return run.id

    app.state.report_service = ReportService(
        SqlAlchemyReportRepository(sessions),
        tasks,
        plans,
        replan_callback=start_replan,
        timezone=settings.timezone,
    )
    app.state.mentor_service = MentorService(
        grant_repo, plans, SqlAlchemyMentorCommentRepository(sessions)
    )
    app.state.admin_service = AdminService(audits)


async def _seed_demo_data(session_factory) -> None:
    async with session_factory() as session:
        users = SqlAlchemyUserRepository(session)
        for identifier, role in (
            ("demo-student", Role.student),
            ("demo-mentor", Role.mentor),
            ("demo-admin", Role.admin),
        ):
            if await users.get_by_identifier(identifier) is None:
                await users.save(
                    UserRecord(
                        id=uuid5(NAMESPACE_URL, f"career-planning/{identifier}"),
                        identifier=identifier,
                        password_hash=hash_password("Demo!2026"),
                        role=role,
                    )
                )
        for scale in build_demo_scales():
            model = await session.get(AssessmentScaleModel, scale.definition.id)
            if model is None:
                model = AssessmentScaleModel(
                    id=scale.definition.id,
                    code=f"demo-{scale.kind}",
                    name=scale.name,
                    kind=scale.kind,
                    version=scale.definition.version,
                    scoring_version=scale.definition.scoring_version,
                    interpretation_version=scale.definition.interpretation_version,
                    license_note="教学演示量表，仅用于职业探索",
                )
                session.add(model)
            for item in scale.items:
                if await session.get(AssessmentItemModel, item.id) is None:
                    session.add(
                        AssessmentItemModel(
                            id=item.id,
                            scale_id=scale.definition.id,
                            dimension=item.dimension,
                            prompt=item.prompt,
                        )
                    )
        for target in build_demo_targets():
            model = await session.get(CareerTarget, target.id)
            if model is None:
                model = CareerTarget(id=target.id, code=target.code)
                session.add(model)
            model.name = target.name
            model.category = target.category
            model.description = target.description
            model.source = target.source
            model.verified_at = target.verified_at
            model.interests = list(target.interests)
            model.values = list(target.values)
            for requirement in target.requirements:
                requirement_model = await session.get(CareerTargetRequirement, requirement.id)
                if requirement_model is None:
                    requirement_model = CareerTargetRequirement(
                        id=requirement.id,
                        target_id=target.id,
                        competency_code=requirement.competency_code,
                    )
                    session.add(requirement_model)
                requirement_model.required_level = requirement.required_level
                requirement_model.hard = requirement.hard
                requirement_model.source = requirement.source
                requirement_model.verified_at = date.fromisoformat(requirement.verified_at)
        await session.commit()

        student_id = uuid5(NAMESPACE_URL, "career-planning/demo-student")
        existing_primary = await session.scalar(
            select(CareerGoal).where(
                CareerGoal.student_id == student_id,
                CareerGoal.primary.is_(True),
            )
        )
        if existing_primary is None:
            first_target = build_demo_targets()[0]
            session.add(
                CareerGoal(
                    id=uuid5(NAMESPACE_URL, "career-planning/demo-goal"),
                    student_id=student_id,
                    target_id=first_target.id,
                    deadline=date(2027, 6, 30),
                    weekly_hours=5,
                    constraints=None,
                    primary=True,
                    created_at=datetime.now(UTC),
                )
            )
            await session.commit()


@asynccontextmanager
async def persistent_lifespan(app):
    await configure_persistent_services(app, app.state.settings)
    try:
        yield
    finally:
        tasks = list(app.state.ai_run_tasks)
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        await app.state.db_sessions.remove()
        await app.state.redis.aclose()
        await app.state.engine.dispose()
