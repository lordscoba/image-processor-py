from app.models.log_model import UsageLog


async def log_action(
    db,
    action_type,
    request,
    success=True,
    status_code=200,
    error_type=None,
    error_message=None,
    file_size=None,
    original_format=None,
    target_format=None,
    width=None,
    height=None,
    processing_time_ms=None,
):
    await UsageLog.create_log(
        db=db,
        action_type=action_type,
        endpoint=str(request.url.path),
        method=request.method,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        request_id=request.headers.get("x-request-id"),
        file_size=file_size,
        original_format=original_format,
        target_format=target_format,
        image_width=width,
        image_height=height,
        success=success,
        status_code=status_code,
        error_type=error_type,
        error_message=error_message,
        processing_time_ms=processing_time_ms,
    )