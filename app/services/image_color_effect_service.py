import io
import time
import numpy as np
from PIL import Image, ImageEnhance,ImageFilter
from fastapi.responses import StreamingResponse
from starlette.concurrency import run_in_threadpool
from app.core.logging import logger
from pillow_lut import load_cube_file
from pathlib import Path



FILTER_PRESETS = {

    "vintage": {
        "brightness": 1.1,
        "contrast": 1.2,
        "saturation": 0.8,
        "temperature": 20
    },

    "cool": {
        "temperature": -30,
        "saturation": 1.1
    },

    "warm": {
        "temperature": 40
    },

    "dramatic": {
        "contrast": 1.5,
        "saturation": 1.2
    },

    "noir": {
        "contrast": 1.7,
        "saturation": 0.0
    },

    "cyberpunk": {
        "contrast": 1.3,
        "saturation": 1.6,
        "temperature": -20
    },

    "faded": {
        "contrast": 0.8,
        "saturation": 0.7,
        "brightness": 1.1
    }

}

LUT_DIRECTORY = Path("app/luts")
def _load_lut(lut_name):

    try:

        for folder in LUT_DIRECTORY.iterdir():

            lut_path = folder / f"{lut_name}.cube"

            if lut_path.exists():
                return load_cube_file(str(lut_path))

        return None

    except Exception as e:
        logger.error(f"LUT load error: {e}")
        return None


def _rotate_hue(img_np, degrees):

    if degrees == 0:
        return img_np

    img = Image.fromarray(img_np.astype(np.uint8), "RGB").convert("HSV")

    hsv = np.array(img)

    hsv[:, :, 0] = (hsv[:, :, 0].astype(int) + degrees) % 255

    return np.array(Image.fromarray(hsv, "HSV").convert("RGB"))


def _apply_color_effects(
    image_bytes,
    brightness,
    contrast,
    saturation,
    hue,
    temperature,
    exposure,
    vibrance,
    tint_color,
    preset,
    intensity,
    lut_filter
):

    start_time = time.perf_counter()

    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    if preset and preset in FILTER_PRESETS:
        p = FILTER_PRESETS[preset]

        brightness *= p.get("brightness", 1)
        contrast *= p.get("contrast", 1)
        saturation *= p.get("saturation", 1)
        temperature += p.get("temperature", 0)

    # BASIC PIL OPERATIONS (fast and memory safe)

    img = ImageEnhance.Brightness(img).enhance(brightness)
    img = ImageEnhance.Contrast(img).enhance(contrast)
    img = ImageEnhance.Color(img).enhance(saturation)

    if exposure != 0:
        factor = 2 ** exposure
        img = ImageEnhance.Brightness(img).enhance(factor)

    img_np = np.array(img).astype(np.float32)

    # TEMPERATURE (warm/cool)

    if temperature != 0:
        img_np[:, :, 0] += temperature
        img_np[:, :, 2] -= temperature

    # HUE ROTATION

    if hue != 0:
        img_np = _rotate_hue(img_np, int(hue))

    # SMART VIBRANCE (protects skin tones)

    if vibrance != 0:

        avg = img_np.mean(axis=2, keepdims=True)

        saturation_map = np.abs(img_np - avg)

        vibrance_factor = vibrance / 100

        img_np += (img_np - avg) * vibrance_factor * (1 - saturation_map / 255)

    # TINT OVERLAY

    if tint_color:

        try:

            tint_color = tint_color.lstrip("#")

            r = int(tint_color[0:2], 16)
            g = int(tint_color[2:4], 16)
            b = int(tint_color[4:6], 16)

            tint = np.array([r, g, b], dtype=np.float32)

            img_np = img_np * (1 - intensity) + tint * intensity

        except Exception:
            logger.warning("Invalid tint color provided")

    # Apply LUT cinematic filter

    if lut_filter:

        lut = _load_lut(lut_filter)

        if lut:

            img = Image.fromarray(img_np)

            img = img.filter(lut)

            img_np = np.array(img)

    img_np = np.clip(img_np, 0, 255).astype(np.uint8)

    result = Image.fromarray(img_np)

    output_buffer = io.BytesIO()

    # WEB OPTIMIZED JPEG

    result.save(
        output_buffer,
        format="JPEG",
        quality=85,
        optimize=True,
        progressive=True
    )

    output_buffer.seek(0)

    processing_time = int((time.perf_counter() - start_time) * 1000)

    return output_buffer, processing_time


async def image_color_effect_service(
    file,
    brightness,
    contrast,
    saturation,
    hue,
    temperature,
    exposure,
    vibrance,
    tint_color,
    preset,
    intensity,
    lut_filter=None
):

    await file.seek(0)
    image_bytes = await file.read()

    output_buffer, processing_time = await run_in_threadpool(
        _apply_color_effects,
        image_bytes,
        brightness,
        contrast,
        saturation,
        hue,
        temperature,
        exposure,
        vibrance,
        tint_color,
        preset,
        intensity,
        lut_filter
    )

    return {
        "response": StreamingResponse(
            output_buffer,
            media_type="image/jpeg",
            headers={
                "Content-Disposition": "attachment; filename=color_effect.jpg"
            }
        ),
        "processing_time_ms": processing_time
    }