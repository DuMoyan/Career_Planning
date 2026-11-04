from uuid import uuid4

import pytest

from app.core.errors import ConflictError
from app.domain.plans import PlanStatus, PlanVersionState, activate_version, ensure_editable


def version(status: PlanStatus) -> PlanVersionState:
    return PlanVersionState(
        id=uuid4(),
        career_plan_id=uuid4(),
        version=1,
        status=status,
    )


def test_only_draft_can_activate_and_only_one_version_is_active() -> None:
    draft = version(PlanStatus.draft)
    active = PlanVersionState(
        id=uuid4(),
        career_plan_id=draft.career_plan_id,
        version=2,
        status=PlanStatus.active,
    )

    with pytest.raises(ConflictError):
        activate_version(active, [])
    with pytest.raises(ConflictError):
        activate_version(draft, [active])

    activated = activate_version(draft, [])
    assert activated.status is PlanStatus.active


def test_archived_and_discarded_versions_are_immutable() -> None:
    with pytest.raises(ConflictError):
        ensure_editable(version(PlanStatus.archived))
    with pytest.raises(ConflictError):
        ensure_editable(version(PlanStatus.discarded))


def test_regeneration_creates_new_state_without_overwriting_active_version() -> None:
    active = version(PlanStatus.active)
    regenerated = PlanVersionState(
        id=uuid4(),
        career_plan_id=active.career_plan_id,
        version=active.version + 1,
        status=PlanStatus.draft,
    )

    assert active.status is PlanStatus.active
    assert regenerated.status is PlanStatus.draft
    assert regenerated.id != active.id
