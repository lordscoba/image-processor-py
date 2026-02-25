from fastapi import HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from app.services.svg_optimizer import optimize_svg_service
from app.utils.svg_validators import validate_svg_safety

async def optimize_svg_controller(file: UploadFile):
    # 1. Validate Extension (Fast)
    if not file.filename.lower().endswith(".svg"):
        raise HTTPException(status_code=400, detail="Only .svg files allowed")

    # 2. Read content once (Memory Efficient)
    content = await file.read()
    
    # 3. Size Check
    if len(content) > 2_000_000: # 2MB Example
        raise HTTPException(status_code=413, detail="File too large")

    svg_text = content.decode("utf-8")
    
    # 4. Security Check
    validate_svg_safety(svg_text)

    # 5. Optimize (Non-blocking)
    optimized_buffer = await optimize_svg_service(svg_text)

    return StreamingResponse(
        optimized_buffer,
        media_type="image/svg+xml",
        headers={"Content-Disposition": f"attachment; filename=min-{file.filename}"}
    )