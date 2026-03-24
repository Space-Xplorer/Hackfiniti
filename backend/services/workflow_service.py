class WorkflowService:
    async def run(self, application_id: int) -> dict:
        return {"application_id": application_id, "status": "running"}
