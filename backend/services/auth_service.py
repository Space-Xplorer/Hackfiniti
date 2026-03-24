class AuthService:
    async def login(self, email: str, password: str) -> dict:
        return {"email": email, "token": "placeholder"}
