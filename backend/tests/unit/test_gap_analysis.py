from uuid import uuid4

from app.domain.gap import GapStatus, TargetRequirement, analyze_gap


def requirement(level: int, *, hard: bool = False) -> TargetRequirement:
    return TargetRequirement(
        id=uuid4(),
        competency_code="programming",
        required_level=level,
        hard=hard,
        source="教学演示岗位数据",
        verified_at="2026-11-03",
    )


def test_missing_evidence_is_unknown_not_zero_score() -> None:
    item = analyze_gap([requirement(3)], {})[0]
    assert item.status is GapStatus.unknown
    assert item.evidence_ids == ()


def test_gap_classification_precedence_and_traceability() -> None:
    evidence_id = uuid4()
    met = analyze_gap([requirement(2)], {"programming": (3, (evidence_id,))})[0]
    hard = analyze_gap([requirement(4, hard=True)], {"programming": (2, (evidence_id,))})[0]
    developable = analyze_gap([requirement(4)], {"programming": (2, (evidence_id,))})[0]

    assert met.status is GapStatus.met
    assert hard.status is GapStatus.hard_unmet
    assert developable.status is GapStatus.developable_gap
    assert met.evidence_ids == (evidence_id,)
    assert met.requirement_source == "教学演示岗位数据"
