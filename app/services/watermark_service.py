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
            rotation = kwargs.get("rotation", 0)

            try:
                font = ImageFont.truetype("app/assets/fonts/Roboto-Bold.ttf", font_size)
            except:
                font = ImageFont.load_default()

            draw = ImageDraw.Draw(watermark_layer)

            bbox = draw.textbbox((0, 0), text, font=font)
            w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]

            # Create separate text image
            text_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            text_draw = ImageDraw.Draw(text_layer)

            rgba_color = ImageColor.getcolor(color, "RGBA")
            rgba_color = (*rgba_color[:3], int(255 * opacity))

            text_draw.text((0, 0), text, font=font, fill=rgba_color)

            # Rotate text if needed
            if rotation:
                text_layer = text_layer.rotate(rotation, expand=True)

            position = _calculate_position(base.size, text_layer.size, kwargs.get("position"))

            watermark_layer.paste(text_layer, position, text_layer)

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