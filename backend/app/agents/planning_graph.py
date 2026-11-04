from dataclasses import dataclass

from app.agents.fallback import build_fallback_plan
from app.agents.model import InvalidModelOutput, ModelFailure
from app.agents.validation import validate_plan
from app.schemas.planning import PlanDraft, PlanningContext, ValidationResult


@dataclass(frozen=True, slots=True)
class PlanningResult:
    plan: PlanDraft
    validation: ValidationResult
    fallback_reason: str | None
    service_version: str
    model_version: str
    prompt_version: str


class PlanningGraph:
    def __init__(self, model=None) -> None:
        self.model = model

    async def run(self, context: PlanningContext) -> PlanningResult:
        if self.model is None:
            return self._fallback(context, "missing_api_key")
        try:
            plan = await self.model.generate(context)
            validation = validate_plan(plan, context)
            if validation.valid:
                return self._result(plan, validation, None)
            plan = await self.model.repair(context, validation.errors)
            validation = validate_plan(plan, context)
            if validation.valid:
                return self._result(plan, validation, None)
            return self._fallback(context, "validation_failed")
        except InvalidModelOutput:
            try:
                plan = await self.model.repair(context, [])
                validation = validate_plan(plan, context)
                if validation.valid:
                    return self._result(plan, validation, None)
            except ModelFailure:
                pass
            return self._fallback(context, "invalid_model_output")
        except ModelFailure as error:
            return self._fallback(context, error.reason)

    def _fallback(self, context: PlanningContext, reason: str) -> PlanningResult:
        plan = build_fallback_plan(context)
        return self._result(plan, validate_plan(plan, context), reason)

    def _result(
        self, plan: PlanDraft, validation: ValidationResult, reason: str | None
    ) -> PlanningResult:
        model = self.model
        return PlanningResult(
            plan=plan,
            validation=validation,
            fallback_reason=reason,
            service_version=getattr(model, "service_version", "planning-service-1"),
            model_version=getattr(model, "model_version", "unavailable"),
            prompt_version=getattr(model, "prompt_version", "planning-prompt-1"),
        )
