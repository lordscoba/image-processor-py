from fastapi import UploadFile, HTTPException
from app.core.config import MAX_FILE_SIZE, ALLOWED_EXTENSIONS, MAX_FILE_SIZE_VIDEO
import io
from PIL import Image
from fastapi import UploadFile, HTTPException
from pillow_heif import register_heif_opener
import pillow_avif

from app.utils.profiler import profile_performance


register_heif_opener()

#Prevent image bomb attacks
Image.MAX_IMAGE_PIXELS = 50_000_000  # ~50MP limit


ALLOWED_FORMATS_MAP = {
    "jpg": "JPEG",
    "jpeg": "JPEG",
    "png": "PNG",
    "webp": "WEBP",
    "heic": "HEIF",
    "heif": "HEIF",
    "tiff": "TIFF",
    "tif": "TIFF",
    "bmp": "BMP",
    "ico": "ICO",
    "gif": "GIF",
    "avif": "AVIF",
}
async def validate_file_size(file: UploadFile):
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large")
    await file.seek(0)

async def validate_file_size_video(file: UploadFile):
    file.file.seek(0, 2)  # move to end
    size = file.file.tell()

    if size > MAX_FILE_SIZE_VIDEO:
        raise HTTPException(
            status_code=413,
            detail="File too large. Maximum allowed size is 50MB."
        )

    file.file.seek(0)

def validate_file_extension(filename: str):
    ext = filename.split(".")[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Unsupported file type")
    


def validate_file_extension(filename: str, allowed_extensions=None):

    if not allowed_extensions:
        allowed_extensions = ALLOWED_EXTENSIONS

    ext = filename.split(".")[-1].lower()

    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"File type .{ext} not supported."
        )
    
@profile_performance
async def validate_real_image(file: UploadFile):
    try:
        await file.seek(0)

        # Read minimal bytes (efficient)
        content = await file.read()

        if not content:
            raise HTTPException(status_code=400, detail="Empty file uploaded.")

        # Use BytesIO (safe + consistent)
        img = Image.open(io.BytesIO(content))

        real_format = (img.format or "").upper()
        if not real_format:
            raise HTTPException(status_code=400, detail="Invalid image format.")

        ext = file.filename.split(".")[-1].lower()
        expected_format = ALLOWED_FORMATS_MAP.get(ext)

        if not expected_format:
            raise HTTPException(
                status_code=400,
                detail=f"Extension .{ext} is not supported."
            )

        # ─── Smart format matching ───────────────────────
        is_match = False

        if expected_format == "HEIF" and real_format in ["HEIC", "HEIF"]:
            is_match = True

        elif expected_format == "JPEG" and real_format in ["JPEG", "MPO"]:
            is_match = True

        elif expected_format == "AVIF" and real_format in ["AVIF", "HEIF"]:
            is_match = True  # 🔥 important AVIF fallback

        elif real_format == expected_format:
            is_match = True

        if not is_match:
            raise HTTPException(
                status_code=400,
                detail=f"Fake file detected. Extension is {ext.upper()}, but actual format is {real_format}."
            )

        # Lightweight validation (faster than verify())
        img.close()

        return True

    except Image.DecompressionBombError:
        raise HTTPException(
            status_code=400,
            detail="Image too large (possible decompression bomb attack)."
        )

    except (IOError, SyntaxError):
        raise HTTPException(
            status_code=400,
            detail="Invalid or corrupted image file."
        )

    except HTTPException:
        raise

    except Exception as e:
        print(f"Validation error: {e}")
        raise HTTPException(
            status_code=400,
            detail="Image validation failed."
        )

    finally:
        await file.seek(0)