import io
import time
import fitz
import zipfile
from fastapi.responses import StreamingResponse
from fastapi import HTTPException
from fastapi.concurrency import run_in_threadpool
from app.core.logging import logger

def _sync_extract_images(file_bytes: bytes):
    """Synchronous CPU-bound task to extract raw images from PDF XRefs."""
    start_time = time.perf_counter()
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        zip_buffer = io.BytesIO()
        
        image_count = 0
        
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for page_index in range(len(doc)):
                # Get list of images on the page
                image_list = doc.get_page_images(page_index)
                
                for img_index, img in enumerate(image_list):
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    ext = base_image["ext"]  # e.g., 'png', 'jpeg'
                    
                    image_count += 1
                    filename = f"page{page_index+1}_img{img_index+1}.{ext}"
                    zip_file.writestr(filename, image_bytes)

        doc.close()
        
        if image_count == 0:
            raise ValueError("No images found in the provided PDF.")

        zip_buffer.seek(0)
        processing_time_ms = int((time.perf_counter() - start_time) * 1000)
        
        return zip_buffer, len(file_bytes), processing_time_ms

    except Exception as e:
        logger.error(f"Sync Extraction Error: {str(e)}")
        raise e

async def extract_pdf_images_service(file):
    try:
        # Standardize file reading based on your previous structure
        if hasattr(file, "read"):
            import inspect
            if inspect.iscoroutinefunction(file.read):
                await file.seek(0)
                original_bytes = await file.read()
            else:
                file.seek(0)
                original_bytes = file.read()
        else:
            original_bytes = file

        # Run in threadpool to prevent blocking the event loop
        zip_output, original_size, processing_time = await run_in_threadpool(
            _sync_extract_images, original_bytes
        )

        return {
            "response": StreamingResponse(
                zip_output,
                media_type="application/zip",
                headers={
                    "Content-Disposition": "attachment; filename=extracted_images.zip"
                }
            ),
            "original_size": original_size,
            "processing_time_ms": processing_time,
        }

    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        logger.error(f"Async Wrapper Extraction Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to extract images from PDF.")