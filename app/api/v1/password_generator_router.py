from fastapi import APIRouter, Query, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.controllers.password_generator_controller import password_generator_controller
from app.core.database import get_db
from app.core.limiter import limiter
from app.core.config import RATE_LIMIT

router = APIRouter()


@router.get("/secure-password-generator")
@limiter.limit(RATE_LIMIT)
async def secure_password_generator(
    request: Request,
    length: int = Query(16, ge=8, le=128, description="Password length"),
    uppercase: bool = Query(True),
    lowercase: bool = Query(True),
    numbers: bool = Query(True),
    symbols: bool = Query(True),
    exclude_chars: str = Query("", description="Characters to exclude"),
    db: AsyncSession = Depends(get_db)
):
    return await password_generator_controller(
        length=length,
        uppercase=uppercase,
        lowercase=lowercase,
        numbers=numbers,
        symbols=symbols,
        exclude_chars=exclude_chars,
        request=request,
        db=db
    )