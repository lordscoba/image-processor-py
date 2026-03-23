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
    # 1. Extract the Real IP from headers
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        # Grabs the first IP in the list (the actual user)
        real_ip = forwarded.split(",")[0].strip()
    else:
        # Fallback to the direct client host if no header exists
        real_ip = request.client.host if request.client else None
    await UsageLog.create_log(
        db=db,
        action_type=action_type,
        endpoint=str(request.url.path),
        method=request.method,
        ip_address=real_ip,
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