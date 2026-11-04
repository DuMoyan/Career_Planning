from datetime import date

from app.agents.fallback import build_fallback_plan
from app.schemas.planning import PlanningContext, PlanningGap


def context() -> PlanningContext:
    return PlanningContext(
        goal_deadline=date(2027, 6, 30),
        weekly_hours=6,
        gaps=[
            PlanningGap(
                competency_code="communication",
                status="developable_gap",
                required_level=3,
                current_level=1,
                source="教学演示岗位数据",
            ),
            PlanningGap(
                competency_code="programming",
                status="hard_unmet",
                required_level=4,
                current_level=2,
                source="教学演示岗位数据",
            ),
            PlanningGap(
                competency_code="research_analysis",
                status="unknown",
                required_level=3,
                current_level=None,
                source="教学演示岗位数据",
            ),
        ],
        input_references={"goal_id": "goal-1", "profile_version": "3"},
    )


def test_fallback_is_deterministic_prioritized_and_within_weekly_budget() -> None:
    first = build_fallback_plan(context())
    second = build_fallback_plan(context())

    assert first == second
    assert first.generation_mode == "rules"
    assert [task.competency_code for task in first.tasks[:2]] == [
        "programming",
        "communication",
    ]
    assert sum(task.weekly_hours for task in first.tasks) <= 6
    assert all(milestone.acceptance_criteria for milestone in first.milestones)


def test_unknown_gap_creates_explicit_verification_task() -> None:
    plan = build_fallback_plan(context())

    verification = next(task for task in plan.tasks if task.competency_code == "research_analysis")
    assert verification.is_verification is True
    assert "research_analysis" in plan.unknowns
    assert verification.source_refs == ["教学演示岗位数据"]
