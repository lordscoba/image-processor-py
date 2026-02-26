import asyncio
from app.core.database import engine
from app.models.base import Base
import app.models  # ensures models are registered

async def init():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

if __name__ == "__main__":
    asyncio.run(init())

# to run migrations use: python -m app.init_db
