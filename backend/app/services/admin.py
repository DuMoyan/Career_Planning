class AdminService:
    def __init__(self, audits) -> None:
        self.audits = audits

    async def overview(self) -> dict:
        events = await self.audits.list_recent()
        return {
            "targets": [
                "software-engineer",
                "data-analyst",
                "product-manager",
                "algorithm-engineer",
            ],
            "scale_versions": ["demo-riasec@1.0", "demo-work-values@1.0"],
            "audits": [
                {
                    "id": event.id,
                    "event_type": event.event_type,
                    "actor_id": event.actor_id,
                    "target_type": event.target_type,
                    "result": event.result,
                    "created_at": event.created_at,
                }
                for event in events
            ],
        }
