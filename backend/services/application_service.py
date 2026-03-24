from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.application import Application


async def create_application(db: AsyncSession, user_id: int, product_type: str) -> Application:
    app = Application(user_id=user_id, product_type=product_type)
    db.add(app)
    await db.commit()
    await db.refresh(app)
    return app


async def list_applications(db: AsyncSession, user_id: int) -> list[Application]:
    result = await db.execute(select(Application).where(Application.user_id == user_id))
    return list(result.scalars().all())


async def get_application(db: AsyncSession, application_id: int, user_id: int) -> Application | None:
    result = await db.execute(
        select(Application).where(Application.id == application_id, Application.user_id == user_id)
    )
    return result.scalar_one_or_none()
