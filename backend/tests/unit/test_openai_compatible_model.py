from datetime import date

import httpx
import pytest

from app.agents.model import InvalidModelOutput, ModelRateLimited
from app.agents.openai_compatible import OpenAICompatiblePlanningModel, build_planning_model
from app.core.config import Settings
from app.schemas.planning import PlanningContext


def _context() -> PlanningContext:
    return PlanningContext(
        goal_deadline=date(2027, 6, 30),
        weekly_hours=5,
        gaps=[],
        input_references={"goal_id": "goal-1"},
    )


def _model(handler) -> OpenAICompatiblePlanningModel:
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return OpenAICompatiblePlanningModel(
        base_url="https://model.example/v1",
        api_key="secret",
        model="planning-model",
        timeout_seconds=2,
        client=client,
    )


@pytest.mark.asyncio
async def test_model_adapter_parses_structured_plan_and_uses_configured_endpoint() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == "https://model.example/v1/chat/completions"
        assert request.headers["Authorization"] == "Bearer secret"
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": (
                                '{"milestones":[],"tasks":[],"sources":["goal-1"],'
                                '"unknowns":[],"risks":[],"generation_mode":"model"}'
                            )
                        }
                    }
                ]
            },
        )

    model = _model(handler)
    plan = await model.generate(_context())
    await model.client.aclose()

    assert plan.generation_mode == "model"
    assert plan.sources == ["goal-1"]


@pytest.mark.asyncio
async def test_model_adapter_maps_rate_limit_and_invalid_output() -> None:
    limited = _model(lambda _request: httpx.Response(429))
    with pytest.raises(ModelRateLimited):
        await limited.generate(_context())
    await limited.client.aclose()

    invalid = _model(
        lambda _request: httpx.Response(
            200, json={"choices": [{"message": {"content": "not-json"}}]}
        )
    )
    with pytest.raises(InvalidModelOutput):
        await invalid.generate(_context())
    await invalid.client.aclose()


def test_model_adapter_is_only_enabled_with_complete_configuration() -> None:
    base = dict(
        _env_file=None,
        database_url="postgresql+asyncpg://u:p@localhost/db",
        redis_url="redis://localhost",
        jwt_secret="s" * 32,
    )
    assert build_planning_model(Settings(**base)) is None
    configured = Settings(
        **base,
        model_base_url="https://model.example/v1",
        model_api_key="secret",
        model_name="planning-model",
    )
    assert isinstance(build_planning_model(configured), OpenAICompatiblePlanningModel)
