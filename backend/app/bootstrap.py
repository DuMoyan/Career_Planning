from datetime import UTC, date, datetime
from uuid import NAMESPACE_URL, uuid4, uuid5

from app.agents.planning_graph import PlanningGraph
from app.core.security import hash_password
from app.domain.access import Role
from app.repositories.ai_runs import InMemoryAIRunRepository
from app.repositories.assessments import InMemoryAssessmentRepository
from app.repositories.audits import InMemoryAuditRepository
from app.repositories.competencies import InMemoryCompetencyRepository
from app.repositories.grants import InMemoryGrantCache, InMemoryGrantRepository
from app.repositories.plans import InMemoryPlanRepository
from app.repositories.profiles import InMemoryProfileRepository
from app.repositories.reports import InMemoryReportRepository
from app.repositories.targets import GoalRecord, InMemoryTargetRepository
from app.repositories.tasks import InMemoryTaskRepository
from app.repositories.users import InMemoryUserRepository, UserRecord
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
from app.services.resumes import MemoryFileStore, ResumeParser, ResumeService
from app.services.targets import GoalService, TargetService
from app.services.tasks import TaskService


def configure_demo_services(app, settings) -> None:
    audits = InMemoryAuditRepository()
    users = InMemoryUserRepository()
    for identifier, role in (
        ("demo-student", Role.student),
        ("demo-mentor", Role.mentor),
        ("demo-admin", Role.admin),
    ):
        users.add(
            UserRecord(
                uuid5(NAMESPACE_URL, f"career-planning/{identifier}"),
                identifier,
                hash_password("Demo!2026"),
                role,
            )
        )
    student_id = uuid5(NAMESPACE_URL, "career-planning/demo-student")
    app.state.auth_service = AuthService(users=users, audits=audits, settings=settings)
    app.state.profile_service = ProfileService(InMemoryProfileRepository())
    grant_repo = InMemoryGrantRepository()
    app.state.grant_service = GrantService(
        repository=grant_repo, cache=InMemoryGrantCache(), audits=audits
    )
    app.state.assessment_service = AssessmentService(
        InMemoryAssessmentRepository(build_demo_scales())
    )
    competencies = InMemoryCompetencyRepository()
    app.state.competency_service = CompetencyService(competencies)
    app.state.resume_service = ResumeService(
        repository=competencies,
        files=MemoryFileStore(),
        parser=ResumeParser(),
        max_bytes=settings.upload_max_bytes,
    )
    targets = InMemoryTargetRepository(build_demo_targets())
    app.state.target_service = TargetService(targets, competencies)
    app.state.goal_service = GoalService(targets)
    target = next(iter(targets.targets.values()))
    goal_id = uuid4()
    targets.goals[goal_id] = GoalRecord(
        goal_id, student_id, target.id, date(2027, 6, 30), 5, None, True, datetime.now(UTC)
    )
    plans = InMemoryPlanRepository()
    tasks = InMemoryTaskRepository()
    app.state.plan_service = PlanService(plans, tasks)
    app.state.task_service = TaskService(tasks, plans)
    context = PlanningContext(
        goal_deadline=date(2027, 6, 30),
        weekly_hours=5,
        gaps=[
            PlanningGap(
                competency_code="programming",
                status="developable_gap",
                required_level=3,
                current_level=2,
                source="教学演示岗位数据",
            )
        ],
        input_references={"goal_id": str(goal_id)},
    )
    app.state.ai_run_service = AIRunService(
        repository=InMemoryAIRunRepository(),
        graph=PlanningGraph(None),
        context_provider=lambda _id: context,
        audits=audits,
    )
    app.state.report_service = ReportService(InMemoryReportRepository(), tasks, plans)
    app.state.mentor_service = MentorService(grant_repo, plans)
    app.state.admin_service = AdminService(audits)
