from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from app.domain.grants import GrantPolicy, GrantScope, MentorGrant

NOW = datetime(2026, 11, 4, 4, 0, tzinfo=UTC)


def make_grant(**changes) -> MentorGrant:
    values = {
        "id": uuid4(),
        "student_id": uuid4(),
        "mentor_id": uuid4(),
        "scopes": frozenset({GrantScope.profile_summary}),
        "expires_at": NOW + timedelta(days=90),
        "revoked_at": None,
    }
    values.update(changes)
    return MentorGrant(**values)


def test_active_in_scope_grant_allows_read() -> None:
    grant = make_grant()

    assert GrantPolicy.can_read(grant, GrantScope.profile_summary, NOW) is True


@pytest.mark.parametrize(
    "grant,scope",
    [
        (None, GrantScope.profile_summary),
        (make_grant(revoked_at=NOW), GrantScope.profile_summary),
        (make_grant(expires_at=NOW), GrantScope.profile_summary),
        (make_grant(), GrantScope.goals),
    ],
)
def test_missing_revoked_expired_or_out_of_scope_grant_denies_read(
    grant: MentorGrant | None, scope: GrantScope
) -> None:
    assert GrantPolicy.can_read(grant, scope, NOW) is False


def test_raw_assessment_answers_are_not_a_valid_scope() -> None:
    with pytest.raises(ValueError):
        GrantScope("assessment_answers")
