from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class ConfirmedEvidence:
    id: UUID
    competency_code: str
    demonstrated_level: int
    confirmed: bool
    deleted: bool
    source_type: str


@dataclass(frozen=True, slots=True)
class CompetencyDimension:
    level: int
    evidence_count: int
    evidence_ids: tuple[UUID, ...]
    source_types: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CompetencyProfileSnapshot:
    dimensions: dict[str, CompetencyDimension]
    data_completeness: float


def calculate_profile(
    evidence: list[ConfirmedEvidence],
    *,
    dictionary_size: int = 9,
) -> CompetencyProfileSnapshot:
    grouped: dict[str, list[ConfirmedEvidence]] = {}
    for item in evidence:
        if not item.confirmed or item.deleted:
            continue
        if not 1 <= item.demonstrated_level <= 4:
            raise ValueError("能力证据等级必须在1至4之间")
        grouped.setdefault(item.competency_code, []).append(item)

    dimensions = {
        code: CompetencyDimension(
            level=max(item.demonstrated_level for item in items),
            evidence_count=len(items),
            evidence_ids=tuple(item.id for item in items),
            source_types=tuple(sorted({item.source_type for item in items})),
        )
        for code, items in sorted(grouped.items())
    }
    completeness = round(min(len(dimensions) / dictionary_size, 1) * 100, 2)
    return CompetencyProfileSnapshot(dimensions=dimensions, data_completeness=completeness)
