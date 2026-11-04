from app.cli.seed import InMemorySeedStore, seed_demo_data
from app.core.security import verify_password


def test_demo_seed_is_idempotent_and_complete() -> None:
    store = InMemorySeedStore()
    first = seed_demo_data(store)
    second = seed_demo_data(store)

    assert (
        first == second == {"users": 3, "scales": 2, "items": 57, "competencies": 9, "targets": 4}
    )
    assert len({user.identifier for user in store.users.values()}) == 3
    assert all(verify_password("Demo!2026", user.password_hash) for user in store.users.values())
    assert sorted(len(scale.items) for scale in store.scales.values()) == [21, 36]
    assert set(store.competencies) == {
        "professional_knowledge",
        "programming",
        "data_analysis",
        "research_analysis",
        "product_requirements",
        "communication",
        "teamwork",
        "project_execution",
        "foreign_language",
    }
