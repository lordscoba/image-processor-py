import io
import time
from PIL import Image, ImageColor, ImageDraw, ImageFont
from fastapi.responses import StreamingResponse
from starlette.concurrency import run_in_threadpool


def _calculate_position(base_size, wm_size, pos_name, margin=20):
    bw, bh = base_size
    ww, wh = wm_size

    positions = {
        "top-left": (margin, margin),
        "top-right": (bw - ww - margin, margin),
        "bottom-left": (margin, bh - wh - margin),
        "bottom-right": (bw - ww - margin, bh - wh - margin),
        "center": ((bw - ww) // 2, (bh - wh) // 2),
    }
    return positions.get(pos_name, positions["bottom-right"])


def _sync_watermark(base_bytes, wm_type, wm_bytes=None, **kwargs):
    start = time.perf_counter()

    with Image.open(io.BytesIO(base_bytes)) as base_img:
        base = base_img.convert("RGBA")

        watermark_layer = Image.new("RGBA", base.size, (0, 0, 0, 0))

        opacity = max(0, min(kwargs.get("opacity", 60), 100)) / 100.0

        if wm_type == "text":
            text = kwargs.get("text") or "© SnappyFix"
            font_size = kwargs.get("font_size", 48)
            color = kwargs.get("color", "#ffffff")

            try:
                font = ImageFont.truetype("app/assets/fonts/Roboto-Bold.ttf", font_size)
            except:
                font = ImageFont.load_default()

            draw = ImageDraw.Draw(watermark_layer)
            bbox = draw.textbbox((0, 0), text, font=font)
            w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]

            position = _calculate_position(base.size, (w, h), kwargs.get("position"))

            rgba_color = ImageColor.getcolor(color, "RGBA")
            rgba_color = (*rgba_color[:3], int(255 * opacity))

            draw.text(position, text, font=font, fill=rgba_color)

        else:
            with Image.open(io.BytesIO(wm_bytes)) as wm_img:
                wm = wm_img.convert("RGBA")

                scale = kwargs.get("scale", 0.3)
                wm = wm.resize(
                    (int(wm.width * scale), int(wm.height * scale)),
                    Image.LANCZOS,
                )

                if kwargs.get("rotation"):
                    wm = wm.rotate(kwargs.get("rotation"), expand=True)

                alpha = wm.split()[3].point(lambda p: int(p * opacity))
                wm.putalpha(alpha)

                position = _calculate_position(base.size, wm.size, kwargs.get("position"))
                watermark_layer.paste(wm, position, wm)

        result = Image.alpha_composite(base, watermark_layer).convert("RGB")

        buffer = io.BytesIO()

        quality_map = {
            "low": 85,
            "medium": 75,
            "high": 60
        }

        result.save(
            buffer,
            format="JPEG",
            quality=quality_map.get(kwargs.get("compression"), 75),
            optimize=True,
            progressive=True,
        )

        buffer.seek(0)

    processing_time = int((time.perf_counter() - start) * 1000)
    return buffer, processing_time


async def watermark_service(file, watermark_type, disposition="inline", watermark_file=None, **kwargs):

    base_bytes = await file.read()
    wm_bytes = await watermark_file.read() if watermark_file else None

    buffer, proc_time = await run_in_threadpool(
        _sync_watermark,
        base_bytes,
        watermark_type,
        wm_bytes,
        **kwargs
    )

    filename = f"watermarked_{file.filename}"
    content_disposition = f'{disposition}; filename="{filename}"'

    return StreamingResponse(
        buffer,
        media_type="image/jpeg",
        headers={
            "Content-Disposition": content_disposition,
            "Access-Control-Expose-Headers": "Content-Disposition"
        }
    )
# import io
# import time
# from PIL import Image, ImageDraw, ImageFont, ImageEnhance
# from fastapi.responses import StreamingResponse
# from starlette.concurrency import run_in_threadpool

# def _calculate_position(base_size, wm_size, pos_name, margin=20):
#     bw, bh = base_size
#     ww, wh = wm_size
#     positions = {
#         "top-left": (margin, margin),
#         "top-right": (bw - ww - margin, margin),
#         "bottom-left": (margin, bh - wh - margin),
#         "bottom-right": (bw - ww - margin, bh - wh - margin),
#         "center": ((bw - ww) // 2, (bh - wh) // 2)
#     }
#     return positions.get(pos_name, positions["bottom-right"])

# def _sync_watermark(base_bytes, wm_type, wm_bytes=None, **kwargs):
#     start_time = time.perf_counter()
    
#     base = Image.open(io.BytesIO(base_bytes)).convert("RGBA")
#     txt_layer = Image.new("RGBA", base.size, (255, 255, 255, 0))
    
#     if wm_type == "text":
#         draw = ImageDraw.Draw(txt_layer)
#         # Use default font if custom isn't loaded
#         font = ImageFont.load_default() 
        
#         text = kwargs.get("text", "© SnappyFix")
#         # Simplified color parsing for hex
#         fill_color = kwargs.get("color", "#ffffff")
#         alpha = int(kwargs.get("opacity", 60) * 2.55)
        
#         # Position logic for text
#         w, h = draw.textbbox((0, 0), text, font=font)[2:]
#         pos = _calculate_position(base.size, (w, h), kwargs.get("position"))
#         draw.text(pos, text, fill=fill_color, font=font)
#         # Apply opacity by merging
#         txt_layer.putalpha(alpha)
        
#     else:
#         wm = Image.open(io.BytesIO(wm_bytes)).convert("RGBA")
#         # Scale
#         scale = kwargs.get("scale", 0.3)
#         wm = wm.resize((int(wm.width * scale), int(wm.height * scale)), Image.LANCZOS)
#         # Rotate
#         if kwargs.get("rotation"):
#             wm = wm.rotate(kwargs.get("rotation"), expand=True)
#         # Opacity
#         alpha = kwargs.get("opacity", 40) / 100.0
#         brightness = ImageEnhance.Brightness(wm.split()[3])
#         wm.putalpha(brightness.enhance(alpha))
        
#         pos = _calculate_position(base.size, wm.size, kwargs.get("position"))
#         txt_layer.paste(wm, pos, wm)

#     # Composite and Compress
#     out = Image.alpha_composite(base, txt_layer).convert("RGB")
#     buf = io.BytesIO()
    
#     qual = {"low": 85, "medium": 65, "high": 40}.get(kwargs.get("compression"), 75)
#     out.save(buf, format="JPEG", quality=qual, optimize=True,progressive=True)
#     buf.seek(0)
    
#     return buf, int((time.perf_counter() - start_time) * 1000)

# async def watermark_service(file, watermark_type,disposition="inline", watermark_file=None, **kwargs):
#     base_bytes = await file.read()
#     wm_bytes = await watermark_file.read() if watermark_file else None
    
#     # buf, proc_time = await run_in_threadpool(
#     #     _sync_watermark, base_bytes, watermark_type, wm_bytes, **kwargs
#     # )

#     buf, proc_time = await run_in_threadpool(
#         _sync_watermark, base_bytes, watermark_type, wm_bytes, **kwargs
#     )

#     filename = f"watermarked_{file.filename}"
#     content_disposition = f"{disposition}; filename={filename}"
    
#     return {
#         "response": StreamingResponse(
#             buf, 
#             media_type="image/jpeg",
#             headers={
#                 "Content-Disposition": content_disposition,
#                 "Access-Control-Expose-Headers": "Content-Disposition" # Important for frontend
#             }
#         ),
#         "original_size": len(base_bytes),
#         "processing_time_ms": proc_time
#     }