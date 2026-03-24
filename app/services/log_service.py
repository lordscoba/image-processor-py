from app.models.log_model import UsageLog
from app.utils.log_data import get_country_from_ip, get_real_ip
from app.utils.profiler import profile_performance

@profile_performance
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
    real_ip = get_real_ip(request)
    country = get_country_from_ip(real_ip) 
    await UsageLog.create_log(
        db=db,
        action_type=action_type,
        endpoint=str(request.url.path),
        method=request.method,
        ip_address=real_ip,
        user_agent=request.headers.get("user-agent"),
        request_id=request.headers.get("x-request-id"),
        country=country,
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