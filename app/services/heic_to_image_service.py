import time
import tempfile
import shutil
from PIL import Image, ImageOps
from pillow_heif import register_heif_opener
from fastapi.responses import StreamingResponse
from fastapi import HTTPException
from starlette.concurrency import run_in_threadpool
from app.core.logging import logger
from app.utils.profiler import profile_performance

register_heif_opener()

# Prevent decompression bomb (adjust if needed)
Image.MAX_IMAGE_PIXELS = 40_000_000

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


def _process_heic_to_image(temp_input_path, target_format, settings):
    start_time = time.perf_counter()

    try:
        img = Image.open(temp_input_path)
        # Normalize orientation
        img = ImageOps.exif_transpose(img)

        # Resize EARLY (in-place, memory efficient)
        img.thumbnail((settings["max_width"], settings["max_width"]))

        # Convert mode only if needed
        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGB")

        # Create temp output file (NOT BytesIO)
        tmp_output = tempfile.NamedTemporaryFile(delete=False, suffix=f".{target_format}")
        tmp_output.close()
        
        if target_format in ["jpg", "jpeg"]:
            img = img.convert("RGB")

            img.save(
                tmp_output.name,
                format="JPEG",
                quality=settings["jpeg_quality"],
                optimize=True,
                progressive=True,
                subsampling=settings["subsampling"],
                dpi=(72, 72),
            )
        else:
            img.save(
                tmp_output.name,
                format="PNG",
                optimize=True,
                compress_level=settings["png_compress"]
            )

        processing_time_ms = int((time.perf_counter() - start_time) * 1000)
        return tmp_output.name, processing_time_ms

    except Exception as e:
        logger.error(f"HEIC Processing Error: {str(e)}")
        raise e


@profile_performance
async def heic_to_image_service(file, target_format: str, compression: str = "high"):
    try:
        settings = IMAGE_COMPRESSION_PRESETS.get(
            compression.lower(),
            IMAGE_COMPRESSION_PRESETS["medium"]
        )

        # Save upload to temp file (NO RAM spike)
        with tempfile.NamedTemporaryFile(delete=False) as tmp_input:
            shutil.copyfileobj(file.file, tmp_input)
            input_path = tmp_input.name

        output_path, processing_time_ms = await run_in_threadpool(
            _process_heic_to_image,
            input_path,
            target_format.lower(),
            settings
        )

        ext = "jpg" if target_format.lower() in ["jpg", "jpeg"] else "png"
        media_type = f"image/{'jpeg' if ext == 'jpg' else 'png'}"

        return {
            "response": StreamingResponse(
                open(output_path, "rb"),
                media_type=media_type,
                headers={
                    "Content-Disposition": f"attachment; filename={file.filename.split('.')[0]}_compressed.{ext}"
                }
            ),
            "processing_time_ms": processing_time_ms,
        }

    except Exception as e:
        logger.error(f"HEIC Wrapper Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Error during HEIC conversion.")


# ==============================
# IMAGE → HEIC (OPTIMIZED)
# ==============================

def _process_image_to_heic(temp_input_path, quality: int):
    start_time = time.perf_counter()

    try:
        img = Image.open(temp_input_path)

        # Convert mode if needed
        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGB")

        tmp_output = tempfile.NamedTemporaryFile(delete=False, suffix=".heic")

        img.save(
            tmp_output,
            format="HEIF",
            quality=quality
        )

        tmp_output.seek(0)

        processing_time_ms = int((time.perf_counter() - start_time) * 1000)

        return tmp_output.name, processing_time_ms

    except Exception as e:
        logger.error(f"HEIC Encoding Error: {str(e)}")
        raise e


@profile_performance
async def image_to_heic_service(file, quality: int):
    try:
        # Save input to disk instead of RAM
        with tempfile.NamedTemporaryFile(delete=False) as tmp_input:
            shutil.copyfileobj(file.file, tmp_input)
            input_path = tmp_input.name

        output_path, processing_time_ms = await run_in_threadpool(
            _process_image_to_heic,
            input_path,
            quality
        )

        return {
            "response": StreamingResponse(
                open(output_path, "rb"),
                media_type="image/heic",
                headers={
                    "Content-Disposition": f"attachment; filename={file.filename.split('.')[0]}.heic"
                }
            ),
            "processing_time_ms": processing_time_ms,
        }

    except Exception as e:
        logger.error(f"Image to HEIC Wrapper Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Error during HEIC encoding.")
# import io
# import time
# from PIL import Image, ImageOps
# from pillow_heif import register_heif_opener
# from fastapi.responses import StreamingResponse
# from fastapi import HTTPException
# from starlette.concurrency import run_in_threadpool
# from app.core.logging import logger
# from app.utils.profiler import profile_performance

# register_heif_opener()

# IMAGE_COMPRESSION_PRESETS = {
#     "low": {
#         "jpeg_quality": 90,
#         "png_compress": 3,
#         "subsampling": 0,
#         "max_width": 4000
#     },
#     "medium": {
#         "jpeg_quality": 75,
#         "png_compress": 6,
#         "subsampling": 1,
#         "max_width": 3000
#     },
#     "high": {
#         "jpeg_quality": 55,
#         "png_compress": 9,
#         "subsampling": 2,
#         "max_width": 2000
#     }
# }


# def _strip_metadata(img: Image.Image) -> Image.Image:
#     """Remove metadata by creating a new canvas and pasting the image."""
#     logger.info(f"Stripping metadata efficiently for {img.size}")
    
#     # Create a brand new image object (no metadata attached)
#     clean_img = Image.new(img.mode, img.size)
    
#     # Copy pixels only (this happens in C, not Python list objects)
#     clean_img.paste(img)
    
#     return clean_img

# def _resize_if_needed(img: Image.Image, max_width: int) -> Image.Image:
#     """Resize large images while maintaining aspect ratio."""
#     if img.width <= max_width:
#         return img

#     ratio = max_width / float(img.width)
#     new_height = int(img.height * ratio)

#     return img.resize((max_width, new_height), Image.LANCZOS)


# def _sync_heic_to_compressed_image(file_bytes: bytes, target_format: str, compression: str):
#     start_time = time.perf_counter()

#     try:
#         settings = IMAGE_COMPRESSION_PRESETS.get(
#             compression.lower(),
#             IMAGE_COMPRESSION_PRESETS["medium"]
#         )

#         img = Image.open(io.BytesIO(file_bytes))

#         # Normalize orientation
#         img = ImageOps.exif_transpose(img)

#         # Convert to RGB
#         if img.mode not in ("RGB", "RGBA"):
#             img = img.convert("RGB")

#         # Remove metadata
#         img = _strip_metadata(img)

#         # Resize large images (major size saver)
#         img = _resize_if_needed(img, settings["max_width"])

#         output_buffer = io.BytesIO()

#         if target_format.lower() in ["jpg", "jpeg"]:
#             img = img.convert("RGB")

#             img.save(
#                 output_buffer,
#                 format="JPEG",
#                 quality=settings["jpeg_quality"],
#                 optimize=True,
#                 progressive=True,          # 🔥 web optimized
#                 subsampling=settings["subsampling"],
#                 dpi=(72, 72)               # normalize DPI
#             )
#         else:
#             img.save(
#                 output_buffer,
#                 format="PNG",
#                 optimize=True,
#                 compress_level=settings["png_compress"]
#             )

#         output_buffer.seek(0)

#         processing_time_ms = int((time.perf_counter() - start_time) * 1000)

#         return output_buffer, len(file_bytes), processing_time_ms

#     except Exception as e:
#         logger.error(f"Sync HEIC Compression Error: {str(e)}")
#         raise e

# @profile_performance
# async def heic_to_image_service(file, target_format: str, compression: str = "high"):
#     try:
#         await file.seek(0)
#         heic_bytes = await file.read()

#         output_buffer, original_size, processing_time_ms = await run_in_threadpool(
#             _sync_heic_to_compressed_image,
#             heic_bytes,
#             target_format,
#             compression
#         )

#         ext = "jpg" if target_format.lower() in ["jpg", "jpeg"] else "png"
#         media_type = f"image/{'jpeg' if ext == 'jpg' else 'png'}"

#         return {
#             "response": StreamingResponse(
#                 output_buffer,
#                 media_type=media_type,
#                 headers={
#                     "Content-Disposition": f"attachment; filename={file.filename.split('.')[0]}_compressed.{ext}"
#                 }
#             ),
#             "original_size": original_size,
#             "processing_time_ms": processing_time_ms,
#         }

#     except Exception as e:
#         logger.error(f"HEIC Compression Wrapper Error: {str(e)}")
#         raise HTTPException(status_code=500, detail="Error during HEIC conversion.")


# # Register allows Pillow to save in HEIF format
# register_heif_opener()

# def _sync_image_to_heic(image_bytes: bytes, quality: int):
#     """Synchronously encodes JPG/PNG bytes into HEIC format."""
#     start_time = time.perf_counter()
#     try:
#         # Load source image
#         img = Image.open(io.BytesIO(image_bytes))
        
#         # Ensure compatible mode (HEIC supports RGB/RGBA)
#         if img.mode not in ("RGB", "RGBA"):
#             img = img.convert("RGB")
            
#         output_buffer = io.BytesIO()
        
#         # Save as HEIF (HEIC)
#         # Quality 80 in HEIC is roughly equivalent to 95 in JPEG
#         img.save(
#             output_buffer, 
#             format="HEIF", 
#             quality=quality
#         )
        
#         output_buffer.seek(0)
#         processing_time_ms = int((time.perf_counter() - start_time) * 1000)
        
#         return output_buffer, len(image_bytes), processing_time_ms

#     except Exception as e:
#         logger.error(f"Sync HEIC Encoding Error: {str(e)}")
#         raise e
# @profile_performance
# async def image_to_heic_service(file, quality: int):
#     try:
#         # Safe Byte Extraction
#         await file.seek(0)
#         image_bytes = await file.read()
        
#         output_buffer, original_size, processing_time_ms = await run_in_threadpool(
#             _sync_image_to_heic, image_bytes, quality
#         )

#         return {
#             "response": StreamingResponse(
#                 output_buffer,
#                 media_type="image/heic",
#                 headers={
#                     "Content-Disposition": f"attachment; filename={file.filename.split('.')[0]}.heic",
#                     "Content-Type": "image/heic"
#                 }
#             ),
#             "original_size": original_size,
#             "processing_time_ms": processing_time_ms,
#         }

#     except Exception as e:
#         logger.error(f"Image to HEIC Wrapper Error: {str(e)}")
#         raise HTTPException(status_code=500, detail="Error during HEIC encoding.")