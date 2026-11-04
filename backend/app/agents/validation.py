from app.schemas.planning import (
    PlanDraft,
    PlanningContext,
    ValidationErrorItem,
    ValidationResult,
)

_PROHIBITED_WORDING = ("诊断", "保证", "必然", "确保录用", "百分之百")


def validate_plan(plan: PlanDraft, context: PlanningContext) -> ValidationResult:
    errors: list[ValidationErrorItem] = []
    for index, milestone in enumerate(plan.milestones):
        if not milestone.acceptance_criteria or not all(milestone.acceptance_criteria):
            errors.append(
                ValidationErrorItem(
                    field=f"milestones.{index}.acceptance_criteria",
                    message="里程碑必须包含可核验的验收标准",
                )
            )
        if milestone.due_date > context.goal_deadline:
            errors.append(
                ValidationErrorItem(
                    field=f"milestones.{index}.due_date", message="里程碑不能晚于目标截止日期"
                )
            )
    for index, task in enumerate(plan.tasks):
        if task.due_date > context.goal_deadline:
            errors.append(
                ValidationErrorItem(
                    field=f"tasks.{index}.due_date", message="任务不能晚于目标截止日期"
                )
            )
        if not task.source_refs:
            errors.append(
                ValidationErrorItem(
                    field=f"tasks.{index}.source_refs", message="任务必须标注依据来源"
                )
            )
        if any(word in task.title for word in _PROHIBITED_WORDING):
            errors.append(
                ValidationErrorItem(
                    field=f"tasks.{index}.title", message="任务包含诊断或结果保证类禁用表述"
                )
            )
    if sum(task.weekly_hours for task in plan.tasks) > context.weekly_hours + 0.001:
        errors.append(
            ValidationErrorItem(field="tasks.weekly_hours", message="每周任务总时长超过可用时间")
        )
    if context.gaps and not plan.sources:
        errors.append(ValidationErrorItem(field="sources", message="计划必须列出事实依据来源"))
    unknown_codes = {gap.competency_code for gap in context.gaps if gap.status == "unknown"}
    if not unknown_codes.issubset(set(plan.unknowns)):
        errors.append(ValidationErrorItem(field="unknowns", message="未知能力必须明确标记并核验"))
    return ValidationResult(valid=not errors, errors=errors)
