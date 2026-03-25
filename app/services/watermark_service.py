import io
import time
from PIL import Image, ImageColor, ImageDraw, ImageFont, ImageEnhance
from fastapi.responses import StreamingResponse
from starlette.concurrency import run_in_threadpool

# ─────────────────────────────────────────────────────────────
# FONT CACHE (huge performance boost)
# ─────────────────────────────────────────────────────────────
FONT_CACHE = {}

def get_font(size):
    if size not in FONT_CACHE:
        try:
            FONT_CACHE[size] = ImageFont.truetype(
                "app/assets/fonts/Roboto-Bold.ttf", size
            )
        except:
            FONT_CACHE[size] = ImageFont.load_default()
    return FONT_CACHE[size]


# ─────────────────────────────────────────────────────────────
# POSITION CALCULATION (clamped)
# ─────────────────────────────────────────────────────────────
def _calculate_position(base_size, wm_size, pos_name, margin=20):
    bw, bh = base_size
    ww, wh = wm_size

    x, y = {
        "top-left": (margin, margin),
        "top-right": (bw - ww - margin, margin),
        "bottom-left": (margin, bh - wh - margin),
        "bottom-right": (bw - ww - margin, bh - wh - margin),
        "center": ((bw - ww) // 2, (bh - wh) // 2),
    }.get(pos_name, (bw - ww - margin, bh - wh - margin))

    # Clamp inside image
    x = max(0, min(x, bw - ww))
    y = max(0, min(y, bh - wh))

    return (x, y)


# ─────────────────────────────────────────────────────────────
# CORE PROCESSOR (optimized)
# ─────────────────────────────────────────────────────────────
def _sync_watermark(base_bytes, wm_type, wm_bytes=None, **kwargs):
    start = time.perf_counter()

    with Image.open(io.BytesIO(base_bytes)) as base_img:
        # Avoid unnecessary conversion
        base = base_img if base_img.mode == "RGBA" else base_img.convert("RGBA")

        opacity = max(0, min(kwargs.get("opacity", 60), 100)) / 100.0

        # ───────── TEXT WATERMARK ─────────
        if wm_type == "text":
            text = kwargs.get("text") or "© SnappyFix"
            font_size = kwargs.get("font_size", 48)
            color = kwargs.get("color", "#ffffff")
            rotation = kwargs.get("rotation", 0)

            font = get_font(font_size)

            # Create dummy draw for bbox
            # dummy_img = Image.new("RGBA", (1, 1))
            # draw = ImageDraw.Draw(dummy_img)

            # bbox = draw.textbbox((0, 0), text, font=font)
            bbox = font.getbbox(text)
            w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]

            # padding = int(font_size * 0.4)

            pad_x = max(10, int(font_size * 0.25))
            pad_y = max(10, int(font_size * 0.4))

            # text_layer = Image.new("RGBA", (w + padding, h + padding), (0, 0, 0, 0))
            text_layer = Image.new(
                "RGBA",
                (w + pad_x, h + pad_y),
                (0, 0, 0, 0)
            )
            text_draw = ImageDraw.Draw(text_layer)

            rgba_color = ImageColor.getcolor(color, "RGBA")
            rgba_color = (*rgba_color[:3], int(255 * opacity))

            text_draw.text(
                (pad_x // 2, pad_y // 2),
                text,
                font=font,
                fill=rgba_color
            )

            if rotation:
                text_layer = text_layer.rotate(rotation, expand=True)

            position = _calculate_position(base.size, text_layer.size, kwargs.get("position"))

            base.paste(text_layer, position, text_layer)

        # ───────── IMAGE WATERMARK ─────────
        else:
            with Image.open(io.BytesIO(wm_bytes)) as wm_img:
                wm = wm_img if wm_img.mode == "RGBA" else wm_img.convert("RGBA")

                scale = kwargs.get("scale", 0.3)

                # Adaptive resampling (faster)
                resample = Image.BILINEAR if scale < 0.5 else Image.LANCZOS

                new_w = int(wm.width * scale)
                new_h = int(wm.height * scale)

                # Prevent oversized watermark
                max_w = int(base.width * 0.9)
                max_h = int(base.height * 0.9)

                if new_w > max_w or new_h > max_h:
                    ratio = min(max_w / new_w, max_h / new_h)
                    new_w = int(new_w * ratio)
                    new_h = int(new_h * ratio)

                wm = wm.resize((new_w, new_h), resample)

                rotation = kwargs.get("rotation", 0)
                if rotation:
                    wm = wm.rotate(rotation, expand=True)

                # Faster opacity handling
                alpha = wm.getchannel("A")
                alpha = ImageEnhance.Brightness(alpha).enhance(opacity)
                wm.putalpha(alpha)

                position = _calculate_position(base.size, wm.size, kwargs.get("position"))

                # 🔥 Paste directly
                base.paste(wm, position, wm)

        # ───────── OUTPUT ─────────
        result = base.convert("RGB")

        buffer = io.BytesIO()

        quality_map = {
            "low": 85,
            "medium": 75,
            "high": 60
        }

        compression = kwargs.get("compression", "medium")
        quality = quality_map.get(compression, 75)

        # Avoid expensive optimize unless needed
        optimize = compression == "high"

        result.save(
            buffer,
            format="JPEG",
            quality=quality,
            optimize=optimize,
            progressive=True,
        )

        buffer.seek(0)

    processing_time = int((time.perf_counter() - start) * 1000)
    return buffer, processing_time


# ─────────────────────────────────────────────────────────────
# ASYNC ENTRY POINT
# ─────────────────────────────────────────────────────────────
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