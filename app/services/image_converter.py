from PIL import Image, ImageOps, UnidentifiedImageError, ImageSequence

import io
import time
from fastapi.responses import StreamingResponse
from fastapi import HTTPException
from app.core.logging import logger
from app.utils.image_validators import validate_image_safety


SUPPORTED_FORMATS = {
    "jpeg": "JPEG",
    "jpg": "JPEG",
    "png": "PNG",
    "webp": "WEBP",
    "bmp": "BMP",
    "tiff": "TIFF",
    "tif": "TIFF",
    "gif": "GIF",
    "ico": "ICO",
    "avif": "AVIF",
}


LOSSY_FORMATS = {"jpeg", "jpg", "webp", "avif"}
TRANSPARENCY_SAFE = {"png", "webp", "avif"}
NO_TRANSPARENCY = {"jpeg", "jpg", "bmp"}


def _prepare_image_for_format(image: Image.Image, target_format: str) -> Image.Image:
    """
    Normalize image mode depending on target format.
    """

    # Remove transparency for formats that don’t support it
    if target_format in NO_TRANSPARENCY:
        if image.mode in ("RGBA", "LA", "P"):
            background = Image.new("RGB", image.size, (255, 255, 255))
            if "A" in image.mode:
                background.paste(image, mask=image.split()[-1])
            else:
                background.paste(image)
            return background
        return image.convert("RGB")

    # Preserve transparency where supported
    if target_format in TRANSPARENCY_SAFE:
        if image.mode not in ("RGB", "RGBA"):
            return image.convert("RGBA")

    # GIF uses palette
    if target_format == "gif":
        return image.convert("P", palette=Image.ADAPTIVE)

    # ICO must be RGBA
    if target_format == "ico":
        return image.convert("RGBA")

    return image


def _save_animated_gif(image: Image.Image, buffer: io.BytesIO):
    frames = []
    for frame in ImageSequence.Iterator(image):
        frames.append(frame.convert("P", palette=Image.ADAPTIVE))

    frames[0].save(
        buffer,
        format="GIF",
        save_all=True,
        append_images=frames[1:],
        loop=0,
        optimize=True,
        duration=image.info.get("duration", 100),
    )


def convert_image(file, target_format: str):
    start_time = time.perf_counter()

    try:
        target_format = target_format.lower()

        if target_format not in SUPPORTED_FORMATS:
            raise HTTPException(
                status_code=400,
                detail=f"Target format '{target_format}' not supported"
            )

        image = Image.open(file)
        validate_image_safety(image)

        original_format = image.format.lower() if image.format else None
        width, height = image.size

        image = ImageOps.exif_transpose(image)

        buffer = io.BytesIO()

        # ---------------------------------
        # Animated GIF preservation
        # ---------------------------------
        if getattr(image, "is_animated", False) and target_format == "gif":
            _save_animated_gif(image, buffer)

        else:
            image = _prepare_image_for_format(image, target_format)

            save_kwargs = {"optimize": True}

            if target_format in LOSSY_FORMATS:
                save_kwargs["quality"] = 90

            if target_format == "ico":
                image.save(
                    buffer,
                    format="ICO",
                    sizes=[(16, 16), (32, 32), (64, 64), (128, 128), (256, 256)]
                )
            else:
                image.save(
                    buffer,
                    format=SUPPORTED_FORMATS[target_format],
                    **save_kwargs
                )

        buffer.seek(0)

        processing_time_ms = int((time.perf_counter() - start_time) * 1000)

        return {
            "response": StreamingResponse(
                buffer,
                media_type=f"image/{target_format}",
                headers={
                    "Content-Disposition": f"attachment; filename=converted.{target_format}"
                }
            ),
            "original_format": original_format,
            "target_format": target_format,
            "width": width,
            "height": height,
            "processing_time_ms": processing_time_ms,
        }

    except UnidentifiedImageError:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is not a valid image."
        )

    except Exception as e:
        logger.error(f"Conversion Error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred during image processing."
        )