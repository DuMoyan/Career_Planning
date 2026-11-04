import inspect
from uuid import UUID, uuid4

from app.core.errors import ConflictError, ForbiddenError
from app.repositories.ai_runs import AIRunRecord
from app.repositories.audits import AuditEvent


class AIRunService:
    def __init__(
        self, *, repository, graph, context_provider, audits, auto_process: bool = True
    ) -> None:
        self.repository = repository
        self.graph = graph
        self.context_provider = context_provider
        self.audits = audits
        self.auto_process = auto_process

    async def create(self, student_id: UUID, parent_run_id: UUID | None = None) -> AIRunRecord:
        if await self.repository.find_running(student_id):
            raise ConflictError("已有规划生成任务正在运行")
        context = self.context_provider(student_id)
        if inspect.isawaitable(context):
            context = await context
        run = AIRunRecord(
            id=uuid4(),
            student_id=student_id,
            status="running",
            input_references=dict(context.input_references),
            parent_run_id=parent_run_id,
            events=[("started", {"status": "running"})],
        )
        await self.repository.save(run)
        await self.audits.append(
            AuditEvent(
                event_type="planning.run.started",
                actor_id=student_id,
                target_type="ai_run",
                target_id=str(run.id),
                result="success",
                metadata={"input_references": run.input_references},
            )
        )
        if self.auto_process:
            result = await self.graph.run(context)
            run.status = "completed"
            run.plan_snapshot = result.plan.model_dump(mode="json")
            run.validation_result = result.validation.model_dump(mode="json")
            run.sources = list(result.plan.sources)
            run.generation_mode = result.plan.generation_mode
            run.fallback_reason = result.fallback_reason
            run.service_version = result.service_version
            run.model_version = result.model_version
            run.prompt_version = result.prompt_version
            run.events.append(
                (
                    "completed",
                    {
                        "status": "completed",
                        "generation_mode": run.generation_mode,
                        "fallback_reason": run.fallback_reason,
                    },
                )
            )
            await self.repository.save(run)
        return run

    async def get(self, student_id: UUID, run_id: UUID) -> AIRunRecord:
        run = await self.repository.get(run_id)
        if run is None or run.student_id != student_id:
            raise ForbiddenError("规划生成记录不存在或无权访问")
        return run

    async def retry(self, student_id: UUID, run_id: UUID) -> AIRunRecord:
        original = await self.get(student_id, run_id)
        if original.status in {"queued", "running"}:
            raise ConflictError("当前规划生成任务尚未结束")
        return await self.create(student_id, parent_run_id=original.id)

    async def events(self, student_id: UUID, run_id: UUID):
        return (await self.get(student_id, run_id)).events


def serialize_run(run: AIRunRecord) -> dict:
    return {
        "id": run.id,
        "status": run.status,
        "generation_mode": run.generation_mode,
        "fallback_reason": run.fallback_reason,
        "service_version": run.service_version,
        "model_version": run.model_version,
        "prompt_version": run.prompt_version,
        "input_references": run.input_references,
        "plan_snapshot": run.plan_snapshot,
        "validation_result": run.validation_result,
        "sources": run.sources,
        "confirmation_status": run.confirmation_status,
        "parent_run_id": run.parent_run_id,
        "error_code": run.error_code,
        "created_at": run.created_at,
        "updated_at": run.updated_at,
    }
