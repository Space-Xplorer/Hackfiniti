class ApplicationService:
    async def create_application(self, user_id: int, product_type: str) -> dict:
        return {"user_id": user_id, "product_type": product_type, "status": "draft"}
