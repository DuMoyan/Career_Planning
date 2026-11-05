import json

import httpx
from pydantic import ValidationError

from app.agents.model import (
    InvalidModelOutput,
    ModelFailure,
    ModelRateLimited,
    ModelTimeout,
)
from app.schemas.planning import PlanDraft, PlanningContext, ValidationErrorItem


class OpenAICompatiblePlanningModel:
    service_version = "openai-compatible-1"
    prompt_version = "planning-prompt-1"

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        timeout_seconds: int,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model_version = model
        self.timeout_seconds = timeout_seconds
        self.client = client

    async def generate(self, context: PlanningContext) -> PlanDraft:
        return await self._request(context, [])

    async def repair(
        self, context: PlanningContext, errors: list[ValidationErrorItem]
    ) -> PlanDraft:
        return await self._request(context, errors)

    async def _request(
        self, context: PlanningContext, errors: list[ValidationErrorItem]
    ) -> PlanDraft:
        instruction = (
            "你是大学生职业规划助手。只输出符合 PlanDraft 结构的 JSON；"
            "不得承诺就业结果，所有任务必须引用输入来源。"
        )
        payload = {
            "model": self.model_version,
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": instruction},
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "context": context.model_dump(mode="json"),
                            "repair_errors": [item.model_dump() for item in errors],
                        },
                        ensure_ascii=False,
                    ),
                },
            ],
        }
        owned_client = self.client is None
        client = self.client or httpx.AsyncClient(timeout=self.timeout_seconds)
        try:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=payload,
            )
            if response.status_code == 429:
                raise ModelRateLimited()
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            data = content if isinstance(content, dict) else json.loads(content)
            return PlanDraft.model_validate(data)
        except httpx.TimeoutException as error:
            raise ModelTimeout() from error
        except (httpx.HTTPError, KeyError, TypeError) as error:
            raise ModelFailure() from error
        except (json.JSONDecodeError, ValidationError) as error:
            raise InvalidModelOutput() from error
        finally:
            if owned_client:
                await client.aclose()


def build_planning_model(settings):
    if not (settings.model_base_url and settings.model_api_key and settings.model_name):
        return None
    return OpenAICompatiblePlanningModel(
        base_url=settings.model_base_url,
        api_key=settings.model_api_key,
        model=settings.model_name,
        timeout_seconds=settings.model_timeout_seconds,
    )
