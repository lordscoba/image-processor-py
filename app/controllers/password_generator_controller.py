from fastapi import HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.password_generator_service import password_generator_service
from app.services.log_service import log_action
from app.enums.action_type import ActionType
from app.core.logging import logger


async def password_generator_controller(
    length: int,
    uppercase: bool,
    lowercase: bool,
    numbers: bool,
    symbols: bool,
    exclude_chars: str,
    request: Request,
    db: AsyncSession,
):
    try:

        logger.info(f"Generating secure password length={length}")

        result_data = await password_generator_service(
            length=length,
            uppercase=uppercase,
            lowercase=lowercase,
            numbers=numbers,
            symbols=symbols,
            exclude_chars=exclude_chars
        )

        logger.info("Secure password generated successfully")

        await log_action(
            db=db,
            action_type=ActionType.PASSWORD_GENERATOR,
            request=request,
            success=True,
            status_code=200,
            file_size=None,
            original_format=None,
            target_format=None,
            width=None,
            height=None,
            processing_time_ms=None,
        )

        return result_data

    except HTTPException as e:

        await log_action(
            db=db,
            action_type=ActionType.PASSWORD_GENERATOR,
            request=request,
            success=False,
            status_code=e.status_code,
            error_type="http_exception",
            error_message=str(e.detail),
        )

        raise e

    except Exception as e:

        logger.error(f"Password generator error: {str(e)}")

        await log_action(
            db=db,
            action_type=ActionType.PASSWORD_GENERATOR,
            request=request,
            success=False,
            status_code=500,
            error_type="internal_error",
            error_message=str(e),
        )

        raise HTTPException(
            status_code=500,
            detail="Password generation failed."
        )