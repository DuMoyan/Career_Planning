from datetime import date

from app.agents.validation import validate_plan
from app.schemas.planning import (
    MilestoneDraft,
    PlanDraft,
    PlanningContext,
    PlanningGap,
    TaskDraft,
)


def valid_context() -> PlanningContext:
    return PlanningContext(
        goal_deadline=date(2027, 6, 30),
        weekly_hours=4,
        gaps=[
            PlanningGap(
                competency_code="programming",
                status="developable_gap",
                required_level=3,
                current_level=2,
                source="岗位样本",
            ),
            PlanningGap(
                competency_code="research_analysis",
                status="unknown",
                required_level=2,
                current_level=None,
                source="岗位样本",
            ),
        ],
        input_references={"goal_id": "goal-1"},
    )


def valid_plan() -> PlanDraft:
    return PlanDraft(
        milestones=[
            MilestoneDraft(
                title="完成能力验证",
                due_date=date(2027, 5, 30),
                acceptance_criteria=["提交一份可复核作品"],
            )
        ],
        tasks=[
            TaskDraft(
                title="完成编程练习",
                competency_code="programming",
                due_date=date(2027, 5, 1),
                weekly_hours=2,
                source_refs=["岗位样本"],
            )
        ],
        sources=["岗位样本"],
        unknowns=["research_analysis"],
        risks=["时间安排可能变化"],
        generation_mode="model",
    )


def test_validation_returns_field_errors_for_structure_deadline_and_load() -> None:
    plan = valid_plan()
    plan.milestones[0].acceptance_criteria = []
    plan.tasks[0].due_date = date(2027, 7, 1)
    plan.tasks[0].weekly_hours = 5

    result = validate_plan(plan, valid_context())

    assert result.valid is False
    assert {error.field for error in result.errors} >= {
        "milestones.0.acceptance_criteria",
        "tasks.0.due_date",
        "tasks.weekly_hours",
    }


def test_validation_rejects_missing_traceability_and_prohibited_claims() -> None:
    plan = valid_plan()
    plan.sources = []
    plan.unknowns = []
    plan.tasks[0].title = "诊断你的职业人格并保证获得录用"

    result = validate_plan(plan, valid_context())

    fields = {error.field for error in result.errors}
    assert "sources" in fields
    assert "unknowns" in fields
    assert "tasks.0.title" in fields
