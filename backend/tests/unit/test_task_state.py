from uuid import uuid4

import pytest

from app.core.errors import ConflictError
from app.domain.plans import PlanStatus
from app.domain.tasks import TaskState, TaskStatus, transition_task


def state(status: TaskStatus, *, plan_status: PlanStatus = PlanStatus.active) -> TaskState:
    return TaskState(
        id=uuid4(),
        status=status,
        plan_status=plan_status,
        check_in_ids=(uuid4(),),
    )


def test_allowed_task_transitions_preserve_check_ins() -> None:
    started = transition_task(state(TaskStatus.todo), TaskStatus.in_progress)
    completed = transition_task(started, TaskStatus.completed)

    assert started.status is TaskStatus.in_progress
    assert completed.status is TaskStatus.completed
    assert completed.check_in_ids == started.check_in_ids


def test_invalid_transition_and_archived_version_mutation_are_rejected() -> None:
    with pytest.raises(ConflictError):
        transition_task(state(TaskStatus.completed), TaskStatus.in_progress)
    with pytest.raises(ConflictError):
        transition_task(
            state(TaskStatus.todo, plan_status=PlanStatus.archived), TaskStatus.in_progress
        )


@pytest.mark.parametrize("target", [TaskStatus.delayed, TaskStatus.abandoned])
def test_delayed_and_abandoned_require_reason(target: TaskStatus) -> None:
    with pytest.raises(ConflictError):
        transition_task(state(TaskStatus.in_progress), target)

    changed = transition_task(state(TaskStatus.in_progress), target, reason="课程考试冲突")
    assert changed.status is target
    assert changed.status_reason == "课程考试冲突"
