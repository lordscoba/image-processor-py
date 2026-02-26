from sqlalchemy import Column, Integer, String, DateTime, Enum, Boolean, Text
from sqlalchemy.sql import func
from app.models.base import Base
from app.enums.action_type import ActionType


class UsageLog(Base):
    __tablename__ = "usage_logs"

    id = Column(Integer, primary_key=True, index=True)

    # Core tracking
    action_type = Column(Enum(ActionType), nullable=False, index=True)
    endpoint = Column(String(255), nullable=True)
    method = Column(String(10), nullable=True)

    # Request info
    ip_address = Column(String(45), nullable=True)  # IPv6 safe
    user_agent = Column(String(500), nullable=True)
    request_id = Column(String(100), nullable=True, index=True)

    # File metadata
    file_size = Column(Integer, nullable=True)
    original_format = Column(String(20), nullable=True)
    target_format = Column(String(20), nullable=True)
    image_width = Column(Integer, nullable=True)
    image_height = Column(Integer, nullable=True)

    # Result tracking
    success = Column(Boolean, default=True, index=True)
    status_code = Column(Integer, nullable=True)
    error_type = Column(String(255), nullable=True)
    error_message = Column(Text, nullable=True)

    # Performance tracking
    processing_time_ms = Column(Integer, nullable=True)

    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # -----------------------
    # DB METHODS
    # -----------------------

    @classmethod
    async def create_log(cls, db, **kwargs):
        log = cls(**kwargs)
        db.add(log)
        await db.commit()
        await db.refresh(log)
        return log

    @classmethod
    async def count_by_action(cls, db, action_type):
        from sqlalchemy import select, func
        result = await db.execute(
            select(func.count()).where(cls.action_type == action_type)
        )
        return result.scalar()

    @classmethod
    async def count_failures(cls, db):
        from sqlalchemy import select, func
        result = await db.execute(
            select(func.count()).where(cls.success == False)
        )
        return result.scalar()

    @classmethod
    async def daily_success_rate(cls, db):
        from sqlalchemy import select, func
        result = await db.execute(
            select(
                func.date(cls.created_at),
                func.count().label("total"),
                func.sum(cls.success.cast(Integer)).label("successful")
            ).group_by(func.date(cls.created_at))
        )
        return result.all()