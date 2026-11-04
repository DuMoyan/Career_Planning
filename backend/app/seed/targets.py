from datetime import date
from uuid import NAMESPACE_URL, uuid5

from app.domain.gap import TargetRequirement
from app.repositories.targets import TargetRecord


def build_demo_targets() -> list[TargetRecord]:
    definitions = (
        (
            "software-engineer",
            "软件开发工程师",
            "技术",
            "设计、开发和维护软件系统",
            ("I", "R", "C"),
            ("成长成就", "自主性", "人际协作"),
            (("programming", 3, True), ("teamwork", 2, False)),
            date(2026, 11, 3),
        ),
        (
            "data-analyst",
            "数据分析师",
            "数据",
            "使用数据支持业务判断",
            ("I", "C", "E"),
            ("成长成就", "社会贡献", "稳定保障"),
            (("data_analysis", 3, True), ("communication", 2, False)),
            date(2026, 11, 3),
        ),
        (
            "product-manager",
            "产品经理",
            "产品",
            "识别需求并协同团队交付产品",
            ("E", "S", "I"),
            ("自主性", "人际协作", "成长成就"),
            (("product_requirements", 3, True), ("communication", 3, False)),
            date(2025, 12, 1),
        ),
        (
            "algorithm-engineer",
            "算法工程师",
            "技术",
            "研究和实现机器学习算法",
            ("I", "R", "C"),
            ("成长成就", "自主性", "经济回报"),
            (("programming", 4, True), ("research_analysis", 3, False)),
            date(2026, 11, 3),
        ),
    )
    records = []
    for (
        code,
        name,
        category,
        description,
        interests,
        values,
        requirements,
        verified_at,
    ) in definitions:
        target_id = uuid5(NAMESPACE_URL, f"career-planning/target/{code}")
        records.append(
            TargetRecord(
                id=target_id,
                code=code,
                name=name,
                category=category,
                description=description,
                source="教学演示岗位数据",
                verified_at=verified_at,
                interests=interests,
                values=values,
                requirements=tuple(
                    TargetRequirement(
                        id=uuid5(target_id, competency_code),
                        competency_code=competency_code,
                        required_level=level,
                        hard=hard,
                        source="教学演示岗位数据",
                        verified_at=verified_at.isoformat(),
                    )
                    for competency_code, level, hard in requirements
                ),
            )
        )
    return records
