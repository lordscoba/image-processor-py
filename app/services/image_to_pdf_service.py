import io
import time
import fitz
from PIL import Image
import zipfile
from fastapi.responses import StreamingResponse
from fastapi import HTTPException
from starlette.concurrency import run_in_threadpool
from app.core.logging import logger

def _sync_image_to_pdf(image_bytes: bytes, filename: str):
    """Synchronously converts image bytes to PDF bytes."""
    start_time = time.perf_counter()
    try:
        # Load image
        img = Image.open(io.BytesIO(image_bytes))
        
        # Convert to RGB (required for PDF if image is PNG with alpha or CMYK)
        if img.mode in ("RGBA", "P", "CMYK"):
            img = img.convert("RGB")
            
        # Create a PDF in memory using PyMuPDF
        pdf_bytes = img.save_all if hasattr(img, 'is_animated') and img.is_animated else None # handle multi-frame if needed
        
        output_buffer = io.BytesIO()
        # PIL can save directly to PDF
        img.save(output_buffer, format="PDF", resolution=100.0, save_all=True)
        
        output_buffer.seek(0)
        processing_time_ms = int((time.perf_counter() - start_time) * 1000)
        
        return output_buffer, len(image_bytes), processing_time_ms

    except Exception as e:
        logger.error(f"Sync Image Conversion Error: {str(e)}")
        raise e

async def image_to_pdf_service(file):
    try:
        # Safe Byte Extraction (Matching your Pro logic)
        await file.seek(0)
        image_bytes = await file.read()
        
        output_buffer, original_size, processing_time_ms = await run_in_threadpool(
            _sync_image_to_pdf, image_bytes, file.filename
        )

        return {
            "response": StreamingResponse(
                output_buffer,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"attachment; filename={file.filename.split('.')[0]}.pdf",
                    "Content-Type": "application/pdf"
                }
            ),
            "original_size": original_size,
            "processing_time_ms": processing_time_ms,
        }

    except Exception as e:
        logger.error(f"Image to PDF Wrapper Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Error during image conversion.")
    

def _sync_pdf_to_images(file_bytes: bytes, img_format: str):
    """Synchronously renders PDF pages to images and zips them."""
    start_time = time.perf_counter()
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        zip_buffer = io.BytesIO()
        
        # Determine image format for PyMuPDF
        ext = "png" if img_format.lower() == "png" else "jpg"
        
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
            for page_index in range(len(doc)):
                page = doc[page_index]
                
                # Increase resolution (2.0 = 2x zoom/DPI)
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                
                img_data = pix.tobytes(ext)
                zip_file.writestr(f"page_{page_index + 1}.{ext}", img_data)

        doc.close()
        zip_buffer.seek(0)
        
        processing_time_ms = int((time.perf_counter() - start_time) * 1000)
        return zip_buffer, len(file_bytes), processing_time_ms

    except Exception as e:
        logger.error(f"Sync PDF to Image Error: {str(e)}")
        raise e

async def pdf_to_image_service(file, img_format: str):
    try:
        await file.seek(0)
        pdf_bytes = await file.read()
        
        zip_buffer, original_size, processing_time_ms = await run_in_threadpool(
            _sync_pdf_to_images, pdf_bytes, img_format
        )

        return {
            "response": StreamingResponse(
                zip_buffer,
                media_type="application/zip",
                headers={
                    "Content-Disposition": f"attachment; filename={file.filename.split('.')[0]}_images.zip"
                }
            ),
            "original_size": original_size,
            "processing_time_ms": processing_time_ms,
        }

    except Exception as e:
        logger.error(f"PDF to Image Wrapper Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Error during image conversion.")