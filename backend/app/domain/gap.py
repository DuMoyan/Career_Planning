from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID


class GapStatus(StrEnum):
    met = "met"
    developable_gap = "developable_gap"
    unknown = "unknown"
    hard_unmet = "hard_unmet"


@dataclass(frozen=True, slots=True)
class TargetRequirement:
    id: UUID
    competency_code: str
    required_level: int
    hard: bool
    source: str
    verified_at: str


@dataclass(frozen=True, slots=True)
class GapItem:
    requirement_id: UUID
    competency_code: str
    required_level: int
    current_level: int | None
    status: GapStatus
    evidence_ids: tuple[UUID, ...]
    requirement_source: str
    verified_at: str


def analyze_gap(
    requirements: list[TargetRequirement],
    profile: dict[str, tuple[int, tuple[UUID, ...]]],
) -> list[GapItem]:
    result = []
    for requirement in requirements:
        current = profile.get(requirement.competency_code)
        if current is None:
            level, evidence_ids, status = None, (), GapStatus.unknown
        else:
            level, evidence_ids = current
            if level >= requirement.required_level:
                status = GapStatus.met
            elif requirement.hard:
                status = GapStatus.hard_unmet
            else:
                status = GapStatus.developable_gap
        result.append(
            GapItem(
                requirement_id=requirement.id,
                competency_code=requirement.competency_code,
                required_level=requirement.required_level,
                current_level=level,
                status=status,
                evidence_ids=evidence_ids,
                requirement_source=requirement.source,
                verified_at=requirement.verified_at,
            )
        )
    return result
