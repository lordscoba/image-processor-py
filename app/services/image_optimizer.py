import zipfile

from PIL import Image, ImageOps, UnidentifiedImageError
import io
from fastapi.responses import StreamingResponse
from fastapi import HTTPException
from app.core.logging import logger
from app.utils.image_validators import validate_image_safety

def detect_avif_support():
    try:
        import pillow_avif
        return True
    except ImportError:
        return False

AVIF_SUPPORTED = detect_avif_support()
    
MAX_ITERATIONS = 10

def strip_metadata(image):
    data = list(image.getdata())
    clean = Image.new(image.mode, image.size)
    clean.putdata(data)
    return clean

def resize_longest_side(image, max_size):
    width, height = image.size
    longest = max(width, height)
    if longest > max_size:
        ratio = max_size / longest
        new_size = (int(width * ratio), int(height * ratio))
        return image.resize(new_size, Image.LANCZOS)
    return image


def compress_to_target(image, target_kb, min_q=20, max_q=95):
    best_buffer = io.BytesIO()
    
    while min_q <= max_q:
        mid_q = (min_q + max_q) // 2
        tmp_buffer = io.BytesIO()
        # Using progressive=True makes JPEGs load better on social media
        image.save(tmp_buffer, format="JPEG", quality=mid_q, optimize=True, progressive=True)
        size_kb = tmp_buffer.tell() / 1024

        if size_kb <= target_kb:
            best_buffer = tmp_buffer # Found a candidate!
            min_q = mid_q + 1
        else:
            max_q = mid_q - 1

    if best_buffer.tell() == 0:
        # Fallback if target_kb is impossible
        image.save(best_buffer, format="JPEG", quality=20, optimize=True)
        
    best_buffer.seek(0)
    return best_buffer


def prepare_image(file):
    try:
        image = Image.open(file)
        image = ImageOps.exif_transpose(image)
        
        # Combined Transparency handling and metadata stripping
        if image.mode in ("RGBA", "P", "LA"):
            background = Image.new("RGB", image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[-1] if image.mode == "RGBA" else None)
            return background
        
        # Simple convert to RGB strips most metadata/ICC profiles
        return image.convert("RGB")
    except Exception as e:
        logger.error(f"Image Preparation Error: {e}")
        raise HTTPException(status_code=400, detail="Invalid image file.")
    

def optimize_for_twitter(file):
    image = prepare_image(file)

    image = resize_longest_side(image, 1600)
    image = image.convert("RGB")

    buffer = compress_to_target(image, target_kb=1000)

    return StreamingResponse(
        buffer,
        media_type="image/jpeg",
        headers={"Content-Disposition": "attachment; filename=twitter.jpg"}
    )

def optimize_for_whatsapp(file):
    image = prepare_image(file)

    image = resize_longest_side(image, 1600)
    image = image.convert("RGB")

    buffer = compress_to_target(image, target_kb=1000)

    return StreamingResponse(
        buffer,
        media_type="image/jpeg",
        headers={"Content-Disposition": "attachment; filename=whatsapp.jpg"}
    )

def optimize_for_web(file):
    image = prepare_image(file)
    image = resize_longest_side(image, 1920)

    buffer = io.BytesIO()
    # WebP often yields 30% smaller files than JPEG at the same quality
    image.save(buffer, format="WEBP", quality=75, method=6, optimize=True)
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="image/webp",
        headers={
            "Content-Disposition": "attachment; filename=optimized_web.webp",
            "Cache-Control": "public, max-age=31536000" # Good for SEO
        }
    )

def optimize_custom(file, target_kb=None, quality=85, resize_percent=None):
    image = prepare_image(file)

    if resize_percent:
        width, height = image.size
        new_size = (int(width * resize_percent / 100), int(height * resize_percent / 100))
        image = image.resize(new_size, Image.LANCZOS)

    if target_kb:
        # Pass min_q=20, max_q=95 properly
        buffer = compress_to_target(image, target_kb)
    else:
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=quality, optimize=True)
        buffer.seek(0)

    return StreamingResponse(buffer, media_type="image/jpeg", headers={"Content-Disposition": "attachment; filename=custom.jpg"})

def optimize_for_instagram(file):
    image = prepare_image(file)

    # Instagram prefers 1080px max
    image = resize_longest_side(image, 1080)

    buffer = io.BytesIO()
    image.save(
        buffer,
        format="JPEG",
        quality=85,
        optimize=True,
        progressive=True
    )
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="image/jpeg",
        headers={"Content-Disposition": "attachment; filename=instagram.jpg"}
    )

def optimize_for_youtube(file):
    image = prepare_image(file)
    # Use 'fit' to maintain aspect ratio without stretching
    image = ImageOps.fit(image, (1280, 720), Image.LANCZOS)

    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=90, optimize=True, progressive=True)
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="image/jpeg", headers={"Content-Disposition": "attachment; filename=youtube.jpg"})


def optimize_for_seo(file):
    image = prepare_image(file)

    sizes = [480, 768, 1200]
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        for size in sizes:
            resized = resize_longest_side(image, size)
            
            buffer = io.BytesIO()
            resized.save(
                buffer,
                format="WEBP",
                quality=75,
                method=6,
                optimize=True
            )
            buffer.seek(0)

            zip_file.writestr(f"image-{size}.webp", buffer.read())

        # AVIF version (if supported)
        if AVIF_SUPPORTED:
            buffer = io.BytesIO()
            image.save(buffer, format="AVIF", quality=50)
            buffer.seek(0)
            zip_file.writestr("image.avif", buffer.read())

    zip_buffer.seek(0)

    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=seo-images.zip"}
    )