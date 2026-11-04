from collections import defaultdict
from dataclasses import dataclass
from uuid import UUID

from app.core.errors import DomainError


class IncompleteAssessment(DomainError):
    code = "INCOMPLETE_ASSESSMENT"

    def __init__(self) -> None:
        super().__init__("请完成全部题目后再提交")


class InvalidAssessmentAnswer(DomainError):
    code = "INVALID_ASSESSMENT_ANSWER"

    def __init__(self) -> None:
        super().__init__("测评答案必须是1至5之间的整数")


@dataclass(frozen=True, slots=True)
class ScaleItem:
    id: UUID
    dimension: str


@dataclass(frozen=True, slots=True)
class ScaleDefinition:
    id: UUID
    version: str
    scoring_version: str
    interpretation_version: str
    items: tuple[ScaleItem, ...]


@dataclass(frozen=True, slots=True)
class ScoreResult:
    dimension_scores: dict[str, float]
    top_dimensions: tuple[str, ...]
    scale_version: str
    scoring_version: str
    interpretation_version: str
    disclaimer: str = "结果仅用于自我探索，不代表能力、心理诊断或确定性职业结论。"


def score_scale(scale: ScaleDefinition, answers: dict[UUID, int]) -> ScoreResult:
    expected_ids = {item.id for item in scale.items}
    if set(answers) != expected_ids:
        raise IncompleteAssessment()
    if any(isinstance(choice, bool) or not 1 <= choice <= 5 for choice in answers.values()):
        raise InvalidAssessmentAnswer()

    grouped: dict[str, list[int]] = defaultdict(list)
    for item in scale.items:
        grouped[item.dimension].append(answers[item.id])
    scores = {
        dimension: round(((sum(values) / len(values)) - 1) * 25, 2)
        for dimension, values in grouped.items()
    }
    ordered = sorted(scores, key=lambda dimension: (-scores[dimension], dimension))
    return ScoreResult(
        dimension_scores=dict(sorted(scores.items())),
        top_dimensions=tuple(ordered[:3]),
        scale_version=scale.version,
        scoring_version=scale.scoring_version,
        interpretation_version=scale.interpretation_version,
    )
