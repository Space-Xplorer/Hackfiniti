from graph.workflow import build_workflow


class WorkflowService:
    async def run(self, application_id: int) -> dict:
        workflow = build_workflow()
        state = {"application_id": application_id, "status": "running", "result": None}
        # When agents are wired into the graph, invoke here: state = await workflow.ainvoke(state)
        return {"application_id": application_id, "status": state["status"]}
