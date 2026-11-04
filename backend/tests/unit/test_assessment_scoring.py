from uuid import uuid4

import pytest

from app.domain.assessment import (
    IncompleteAssessment,
    ScaleDefinition,
    ScaleItem,
    score_scale,
)


def make_scale() -> ScaleDefinition:
    return ScaleDefinition(
        id=uuid4(),
        version="1.0",
        scoring_version="1.0",
        interpretation_version="1.0",
        items=(
            ScaleItem(id=uuid4(), dimension="R"),
            ScaleItem(id=uuid4(), dimension="R"),
            ScaleItem(id=uuid4(), dimension="I"),
        ),
    )


@pytest.mark.parametrize(
    ("choice", "expected"),
    [(1, 0.0), (3, 50.0), (5, 100.0)],
)
def test_likert_choice_normalizes_to_zero_to_one_hundred(
    choice: int, expected: float
) -> None:
    scale = make_scale()
    answers = {item.id: choice for item in scale.items}

    result = score_scale(scale, answers)

    assert result.dimension_scores == {"I": expected, "R": expected}


def test_incomplete_answers_are_rejected() -> None:
    scale = make_scale()

    with pytest.raises(IncompleteAssessment):
        score_scale(scale, {scale.items[0].id: 5})


def test_same_scale_version_and_answers_produce_same_result() -> None:
    scale = make_scale()
    answers = {item.id: 4 for item in scale.items}

    first = score_scale(scale, answers)
    second = score_scale(scale, answers)

    assert first == second
    assert first.scale_version == "1.0"
    assert first.top_dimensions == ("I", "R")
