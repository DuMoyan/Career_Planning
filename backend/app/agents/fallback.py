from datetime import timedelta

from app.schemas.planning import MilestoneDraft, PlanDraft, PlanningContext, TaskDraft

_PRIORITY = {"hard_unmet": 0, "developable_gap": 1, "unknown": 2, "met": 3}


def build_fallback_plan(context: PlanningContext) -> PlanDraft:
    actionable = sorted(
        (gap for gap in context.gaps if gap.status != "met"),
        key=lambda gap: (_PRIORITY[gap.status], gap.competency_code),
    )
    per_task_hours = round(context.weekly_hours / max(len(actionable), 1), 2)
    tasks = []
    for index, gap in enumerate(actionable):
        verification = gap.status == "unknown"
        tasks.append(
            TaskDraft(
                title=(
                    f"核验 {gap.competency_code} 的现有能力证据"
                    if verification
                    else f"提升 {gap.competency_code} 至岗位要求等级"
                ),
                competency_code=gap.competency_code,
                due_date=context.goal_deadline
                - timedelta(days=max(7, 14 * (len(actionable) - index))),
                weekly_hours=per_task_hours,
                source_refs=[gap.source],
                is_verification=verification,
            )
        )
    sources = sorted({gap.source for gap in actionable})
    unknowns = sorted(gap.competency_code for gap in actionable if gap.status == "unknown")
    milestones = [
        MilestoneDraft(
            title="完成目标能力差距验证与提升",
            due_date=context.goal_deadline,
            acceptance_criteria=["所有任务均提交可复核成果或证据，并完成自评记录"],
        )
    ]
    return PlanDraft(
        milestones=milestones,
        tasks=tasks,
        sources=sources,
        unknowns=unknowns,
        risks=["规则方案基于当前证据，资料变化后需要重新评估"],
        generation_mode="rules",
    )
