from uuid import NAMESPACE_URL, uuid5

from app.domain.assessment import ScaleDefinition, ScaleItem
from app.repositories.assessments import AssessmentScale, AssessmentScaleItem


def build_demo_scales() -> list[AssessmentScale]:
    return [
        _build_scale(
            code="demo-riasec",
            name="职业兴趣探索",
            kind="interest",
            dimensions=("R", "I", "A", "S", "E", "C"),
            items_per_dimension=6,
        ),
        _build_scale(
            code="demo-work-values",
            name="职业价值观探索",
            kind="work_values",
            dimensions=(
                "成长成就",
                "自主性",
                "稳定保障",
                "经济回报",
                "社会贡献",
                "人际协作",
                "工作生活平衡",
            ),
            items_per_dimension=3,
        ),
    ]


def _build_scale(
    *, code: str, name: str, kind: str, dimensions: tuple[str, ...], items_per_dimension: int
) -> AssessmentScale:
    scale_id = uuid5(NAMESPACE_URL, f"career-planning/{code}/1.0")
    catalog_items: list[AssessmentScaleItem] = []
    domain_items: list[ScaleItem] = []
    for dimension in dimensions:
        for number in range(1, items_per_dimension + 1):
            item_id = uuid5(scale_id, f"{dimension}/{number}")
            domain_items.append(ScaleItem(id=item_id, dimension=dimension))
            catalog_items.append(
                AssessmentScaleItem(
                    id=item_id,
                    dimension=dimension,
                    prompt=f"我重视或愿意探索“{dimension}”相关体验（第{number}题）",
                )
            )
    return AssessmentScale(
        definition=ScaleDefinition(
            id=scale_id,
            version="1.0",
            scoring_version="1.0",
            interpretation_version="1.0",
            items=tuple(domain_items),
        ),
        name=name,
        kind=kind,
        items=tuple(catalog_items),
    )
