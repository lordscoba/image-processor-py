import io
import time
from PIL import Image, ImageOps
from pillow_heif import register_heif_opener
from fastapi.responses import StreamingResponse
from fastapi import HTTPException
from starlette.concurrency import run_in_threadpool
from app.core.logging import logger
from app.utils.profiler import profile_performance

register_heif_opener()

IMAGE_COMPRESSION_PRESETS = {
    "low": {
        "jpeg_quality": 90,
        "png_compress": 3,
        "subsampling": 0,
        "max_width": 4000
    },
    "medium": {
        "jpeg_quality": 75,
        "png_compress": 6,
        "subsampling": 1,
        "max_width": 3000
    },
    "high": {
        "jpeg_quality": 55,
        "png_compress": 9,
        "subsampling": 2,
        "max_width": 2000
    }
}


def _strip_metadata(img: Image.Image) -> Image.Image:
    """Remove EXIF and metadata safely."""
    data = list(img.getdata())
    clean_img = Image.new(img.mode, img.size)
    clean_img.putdata(data)
    return clean_img


def _resize_if_needed(img: Image.Image, max_width: int) -> Image.Image:
    """Resize large images while maintaining aspect ratio."""
    if img.width <= max_width:
        return img

    ratio = max_width / float(img.width)
    new_height = int(img.height * ratio)

    return img.resize((max_width, new_height), Image.LANCZOS)


def _sync_heic_to_compressed_image(file_bytes: bytes, target_format: str, compression: str):
    start_time = time.perf_counter()

    try:
        settings = IMAGE_COMPRESSION_PRESETS.get(
            compression.lower(),
            IMAGE_COMPRESSION_PRESETS["medium"]
        )

        img = Image.open(io.BytesIO(file_bytes))

        # Normalize orientation
        img = ImageOps.exif_transpose(img)

        # Convert to RGB
        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGB")

        # Remove metadata
        img = _strip_metadata(img)

        # Resize large images (major size saver)
        img = _resize_if_needed(img, settings["max_width"])

        output_buffer = io.BytesIO()

        if target_format.lower() in ["jpg", "jpeg"]:
            img = img.convert("RGB")

            img.save(
                output_buffer,
                format="JPEG",
                quality=settings["jpeg_quality"],
                optimize=True,
                progressive=True,          # 🔥 web optimized
                subsampling=settings["subsampling"],
                dpi=(72, 72)               # normalize DPI
            )
        else:
            img.save(
                output_buffer,
                format="PNG",
                optimize=True,
                compress_level=settings["png_compress"]
            )

        output_buffer.seek(0)

        processing_time_ms = int((time.perf_counter() - start_time) * 1000)

        return output_buffer, len(file_bytes), processing_time_ms

    except Exception as e:
        logger.error(f"Sync HEIC Compression Error: {str(e)}")
        raise e

@profile_performance
async def heic_to_image_service(file, target_format: str, compression: str = "high"):
    try:
        await file.seek(0)
        heic_bytes = await file.read()

        output_buffer, original_size, processing_time_ms = await run_in_threadpool(
            _sync_heic_to_compressed_image,
            heic_bytes,
            target_format,
            compression
        )

        ext = "jpg" if target_format.lower() in ["jpg", "jpeg"] else "png"
        media_type = f"image/{'jpeg' if ext == 'jpg' else 'png'}"

        return {
            "response": StreamingResponse(
                output_buffer,
                media_type=media_type,
                headers={
                    "Content-Disposition": f"attachment; filename={file.filename.split('.')[0]}_compressed.{ext}"
                }
            ),
            "original_size": original_size,
            "processing_time_ms": processing_time_ms,
        }

    except Exception as e:
        logger.error(f"HEIC Compression Wrapper Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Error during HEIC conversion.")


# Register allows Pillow to save in HEIF format
register_heif_opener()

def _sync_image_to_heic(image_bytes: bytes, quality: int):
    """Synchronously encodes JPG/PNG bytes into HEIC format."""
    start_time = time.perf_counter()
    try:
        # Load source image
        img = Image.open(io.BytesIO(image_bytes))
        
        # Ensure compatible mode (HEIC supports RGB/RGBA)
        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGB")
            
        output_buffer = io.BytesIO()
        
        # Save as HEIF (HEIC)
        # Quality 80 in HEIC is roughly equivalent to 95 in JPEG
        img.save(
            output_buffer, 
            format="HEIF", 
            quality=quality
        )
        
        output_buffer.seek(0)
        processing_time_ms = int((time.perf_counter() - start_time) * 1000)
        
        return output_buffer, len(image_bytes), processing_time_ms

    except Exception as e:
        logger.error(f"Sync HEIC Encoding Error: {str(e)}")
        raise e
@profile_performance
async def image_to_heic_service(file, quality: int):
    try:
        # Safe Byte Extraction
        await file.seek(0)
        image_bytes = await file.read()
        
        output_buffer, original_size, processing_time_ms = await run_in_threadpool(
            _sync_image_to_heic, image_bytes, quality
        )

        return {
            "response": StreamingResponse(
                output_buffer,
                media_type="image/heic",
                headers={
                    "Content-Disposition": f"attachment; filename={file.filename.split('.')[0]}.heic",
                    "Content-Type": "image/heic"
                }
            ),
            "original_size": original_size,
            "processing_time_ms": processing_time_ms,
        }

    except Exception as e:
        logger.error(f"Image to HEIC Wrapper Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Error during HEIC encoding.")