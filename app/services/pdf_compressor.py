import fitz
import io
import time
from PIL import Image
from fastapi.responses import StreamingResponse
from fastapi import HTTPException
from fastapi.concurrency import run_in_threadpool
from app.core.logging import logger


COMPRESSION_PRESETS = {
    "low": {"scale": 1.0, "quality": 85},
    "medium": {"scale": 0.6, "quality": 60},
    "high": {"scale": 0.4, "quality": 40},
}


def _sync_compress_pdf(file_bytes: bytes, compression_level: str):
    start_time = time.perf_counter()

    settings = COMPRESSION_PRESETS.get(compression_level.lower())
    if not settings:
        raise ValueError("Invalid compression level")

    scale = settings["scale"]
    quality = settings["quality"]

    try:
        # Open from bytes
        doc = fitz.open(stream=file_bytes, filetype="pdf")

        for page in doc:
            # get_images returns a list of tuples
            image_list = page.get_images(full=True)

            for img in image_list:
                xref = img[0]  # The 'xref' index of the image
                
                # Extract image data
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]

                # Load into PIL for processing
                image = Image.open(io.BytesIO(image_bytes))

                # Calculate new dimensions
                new_width = int(image.width * scale)
                new_height = int(image.height * scale)

                # Skip if already tiny or would become invisible
                if new_width < 50 or new_height < 50:
                    continue 

                # Resize
                image = image.resize((new_width, new_height), Image.LANCZOS)

                # Ensure RGB for JPEG (removes alpha channel issues)
                if image.mode != "RGB":
                    image = image.convert("RGB")

                # Save compressed image to buffer
                img_buffer = io.BytesIO()
                image.save(
                    img_buffer,
                    format="JPEG",
                    quality=quality,
                    optimize=True
                )
                img_buffer.seek(0)

                # CORRECTED LINE: Use page.replace_image instead of doc.update_image
                page.replace_image(xref, stream=img_buffer.read())

        # Finalize and Save
        output_buffer = io.BytesIO()
        doc.save(
            output_buffer,
            garbage=4,
            deflate=True,
            clean=True,
        )
        doc.close()
        
        output_buffer.seek(0)
        processing_time_ms = int((time.perf_counter() - start_time) * 1000)

        return output_buffer, len(file_bytes), processing_time_ms

    except Exception as e:
        logger.error(f"Aggressive Compression Error: {str(e)}")
        raise e


async def compress_pdf_file(file, compression_level: str):
    try:
        # IMPORTANT: file is already a file-like object
        file.seek(0)
        file_bytes = file.read()  # NO await here

        output_buffer, original_size, processing_time_ms = await run_in_threadpool(
            _sync_compress_pdf,
            file_bytes,
            compression_level
        )

        return {
            "response": StreamingResponse(
                output_buffer,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": "attachment; filename=compressed.pdf"
                }
            ),
            "original_size": original_size,
            "processing_time_ms": processing_time_ms,
        }

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))

    except Exception as e:
        logger.error(f"Async Wrapper Error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error during PDF processing."
        )

def _sync_pro_compression(file_bytes: bytes, quality: int, dpi: int):
    """Heavy CPU-bound PDF processing logic."""
    start_time = time.perf_counter()
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        doc.set_metadata({}) # Strip metadata for Pro version

        for page in doc:
            image_list = page.get_images(full=True)
            for img in image_list:
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                
                # Open with PIL
                img_obj = Image.open(io.BytesIO(image_bytes))
                
                # Calculate scaling factor based on 300 DPI as baseline
                # Note: This is a simplified ratio; usually PDFs are 72 points per inch
                scaling_factor = dpi / 300.0
                if scaling_factor >= 1.0:
                    continue # Don't upscale
                
                new_size = (
                    max(1, int(img_obj.width * scaling_factor)),
                    max(1, int(img_obj.height * scaling_factor))
                )

                # Only resize if it's actually a significant change
                img_obj = img_obj.resize(new_size, Image.LANCZOS)

                if img_obj.mode != "RGB":
                    img_obj = img_obj.convert("RGB")

                img_buffer = io.BytesIO()
                img_obj.save(img_buffer, format="JPEG", quality=quality, optimize=True)
                img_buffer.seek(0)

                # FIX: Use page.replace_image instead of doc.update_stream
                page.replace_image(xref, stream=img_buffer.read())

        output_buffer = io.BytesIO()
        doc.save(
            output_buffer,
            garbage=4,
            deflate=True,
            clean=True,
        )
        doc.close()
        output_buffer.seek(0)
        
        processing_time_ms = int((time.perf_counter() - start_time) * 1000)
        return output_buffer, processing_time_ms

    except Exception as e:
        logger.error(f"Sync Pro Compression Logic Error: {str(e)}")
        raise e

async def compress_pdf_pro_service(file, quality: int, dpi: int):
    try:
        # Input Validation
        if not (30 <= quality <= 95):
            raise HTTPException(status_code=400, detail="Quality must be 30-95")
        if not (72 <= dpi <= 300):
            raise HTTPException(status_code=400, detail="DPI must be 72-300")

        # ---------------------------------------------------------
        # SAFE BYTE EXTRACTION
        # ---------------------------------------------------------
        if hasattr(file, "read"):
            # Check if it's an async FastAPI UploadFile
            import inspect
            if inspect.iscoroutinefunction(file.read):
                await file.seek(0)
                original_bytes = await file.read()
            else:
                # It's a standard file-like object
                file.seek(0)
                original_bytes = file.read()
        else:
            # It's already bytes
            original_bytes = file

        original_size = len(original_bytes)

        # Offload to thread pool
        output_buffer, processing_time_ms = await run_in_threadpool(
            _sync_pro_compression, original_bytes, quality, dpi
        )
        return {
            "response": StreamingResponse(
                output_buffer,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": "attachment; filename=compressed-pro.pdf",
                    "Content-Type": "application/pdf"
                }
            ),
            "original_size": original_size,
            "processing_time_ms": processing_time_ms,
        }

    except Exception as e:
        logger.error(f"PRO Compression Wrapper Error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred during advanced compression: {str(e)}"
        )