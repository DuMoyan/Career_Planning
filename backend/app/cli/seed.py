from dataclasses import dataclass
from uuid import NAMESPACE_URL, UUID, uuid5

from app.core.security import hash_password
from app.domain.access import Role
from app.seed.assessments import build_demo_scales
from app.seed.targets import build_demo_targets

COMPETENCIES = (
    "professional_knowledge",
    "programming",
    "data_analysis",
    "research_analysis",
    "product_requirements",
    "communication",
    "teamwork",
    "project_execution",
    "foreign_language",
)


@dataclass(frozen=True, slots=True)
class SeedUser:
    id: UUID
    identifier: str
    password_hash: str
    role: Role


class InMemorySeedStore:
    def __init__(self) -> None:
        self.users: dict[str, SeedUser] = {}
        self.scales = {}
        self.competencies: dict[str, str] = {}
        self.targets = {}


def seed_demo_data(store: InMemorySeedStore) -> dict[str, int]:
    for identifier, role in (
        ("demo-student", Role.student),
        ("demo-mentor", Role.mentor),
        ("demo-admin", Role.admin),
    ):
        if identifier not in store.users:
            store.users[identifier] = SeedUser(
                uuid5(NAMESPACE_URL, f"career-planning/{identifier}"),
                identifier,
                hash_password("Demo!2026"),
                role,
            )
    for scale in build_demo_scales():
        store.scales[scale.definition.id] = scale
    for code in COMPETENCIES:
        store.competencies[code] = code
    for target in build_demo_targets():
        store.targets[target.id] = target
    return {
        "users": len(store.users),
        "scales": len(store.scales),
        "items": sum(len(scale.items) for scale in store.scales.values()),
        "competencies": len(store.competencies),
        "targets": len(store.targets),
    }


def main() -> None:
    counts = seed_demo_data(InMemorySeedStore())
    print("演示数据准备完成：" + "，".join(f"{key}={value}" for key, value in counts.items()))


if __name__ == "__main__":
    main()
