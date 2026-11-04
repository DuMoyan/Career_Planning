from uuid import uuid4

from app.domain.competency import ConfirmedEvidence, calculate_profile


def evidence(code: str, level: int, *, confirmed: bool = True, deleted: bool = False):
    return ConfirmedEvidence(
        id=uuid4(),
        competency_code=code,
        demonstrated_level=level,
        confirmed=confirmed,
        deleted=deleted,
        source_type="project",
    )


def test_highest_confirmed_evidence_level_wins_and_sources_are_retained() -> None:
    first = evidence("programming", 2)
    strongest = evidence("programming", 4)

    profile = calculate_profile([first, strongest])

    assert profile.dimensions["programming"].level == 4
    assert profile.dimensions["programming"].evidence_ids == (first.id, strongest.id)


def test_unconfirmed_and_deleted_evidence_are_ignored() -> None:
    valid = evidence("communication", 2)

    profile = calculate_profile(
        [
            valid,
            evidence("communication", 4, confirmed=False),
            evidence("communication", 3, deleted=True),
        ]
    )

    assert profile.dimensions["communication"].level == 2
    assert profile.dimensions["communication"].evidence_count == 1


def test_more_low_level_evidence_does_not_inflate_demonstrated_level() -> None:
    profile = calculate_profile([evidence("analysis", 1) for _ in range(5)])

    assert profile.dimensions["analysis"].level == 1
    assert profile.dimensions["analysis"].evidence_count == 5
