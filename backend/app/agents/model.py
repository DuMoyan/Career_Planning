from typing import Protocol

from app.schemas.planning import PlanDraft, PlanningContext, ValidationErrorItem


class ModelFailure(Exception):
    reason = "model_failure"


class MissingModelKey(ModelFailure):
    reason = "missing_api_key"


class ModelTimeout(ModelFailure):
    reason = "model_timeout"


class ModelRateLimited(ModelFailure):
    reason = "rate_limited"


class InvalidModelOutput(ModelFailure):
    reason = "invalid_model_output"


class ModelAdapter(Protocol):
    service_version: str
    model_version: str
    prompt_version: str

    async def generate(self, context: PlanningContext) -> PlanDraft: ...
    async def repair(
        self, context: PlanningContext, errors: list[ValidationErrorItem]
    ) -> PlanDraft: ...
