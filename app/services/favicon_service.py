import io
import json
import zipfile
from fastapi.responses import StreamingResponse
from fastapi import HTTPException
from fastapi.concurrency import run_in_threadpool
from PIL import Image, ImageOps
from app.utils.image_validators import validate_image_safety

# Decompression bomb guard (50MP limit)
Image.MAX_IMAGE_PIXELS = 50_000_000

FAVICON_SIZES = [16, 32, 48, 64, 180, 192, 512]
ALLOWED_OUTPUT_EXT = {"ico", "png", "webp"}  # Removed SVG


# ------------------------------------------------
# Helpers
# ------------------------------------------------

def _trim_transparency(img: Image.Image):
    bbox = img.getbbox()
    return img.crop(bbox) if bbox else img


def _detect_brand_color(img: Image.Image) -> str:
    small = img.resize((50, 50)).convert("RGBA")
    pixels = [p[:3] for p in small.getdata() if p[3] > 128]

    if not pixels:
        return "#ffffff"

    r = sum(p[0] for p in pixels) // len(pixels)
    g = sum(p[1] for p in pixels) // len(pixels)
    b = sum(p[2] for p in pixels) // len(pixels)

    return f"#{r:02x}{g:02x}{b:02x}"


def _safe_square_canvas(img, padding, background):
    width, height = img.size
    max_dim = max(width, height)
    square_size = max_dim + padding * 2

    if background == "transparent":
        bg_color = (0, 0, 0, 0)
    else:
        bg_color = background

    canvas = Image.new("RGBA", (square_size, square_size), bg_color)

    x = (square_size - width) // 2
    y = (square_size - height) // 2

    canvas.paste(img, (x, y), img)
    return canvas


def _generate_manifest(brand_color, background_color):
    manifest_dict = {
        "name": "Website",
        "short_name": "Site",
        "icons": [
            {
                "src": "favicon-192x192.png",
                "sizes": "192x192",
                "type": "image/png"
            },
            {
                "src": "favicon-512x512.png",
                "sizes": "512x512",
                "type": "image/png",
                "purpose": "maskable"
            }
        ],
        "theme_color": brand_color,
        "background_color": background_color,
        "display": "standalone"
    }

    return json.dumps(manifest_dict, indent=2)


def _generate_html(extension):
    return f"""
<!-- Standard favicon -->
<link rel="icon" type="image/{extension}" sizes="32x32" href="/favicon-32x32.{extension}">
<link rel="icon" type="image/{extension}" sizes="16x16" href="/favicon-16x16.{extension}">

<!-- Apple -->
<link rel="apple-touch-icon" sizes="180x180" href="/favicon-180x180.{extension}">

<!-- Android -->
<link rel="manifest" href="/site.webmanifest">

<!-- Open Graph -->
<meta property="og:image" content="/social-preview-1200x630.png">
"""


def _build_zip(canvas, image, extension, padding, background, brand_color):

    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:

        for size in FAVICON_SIZES:
            resized = canvas.resize((size, size), Image.LANCZOS)

            with io.BytesIO() as buf:
                if extension == "ico":
                    resized.save(buf, format="PNG")
                    filename = f"favicon-{size}x{size}.png"
                else:
                    resized.save(buf, format=extension.upper())
                    filename = f"favicon-{size}x{size}.{extension}"

                zip_file.writestr(filename, buf.getvalue())

        # Multi-resolution ICO
        with io.BytesIO() as buf:
            canvas.save(
                buf,
                format="ICO",
                sizes=[(16, 16), (32, 32), (48, 48), (64, 64)]
            )
            zip_file.writestr("favicon.ico", buf.getvalue())

        # Dark mode variant (fixed LANCZOS)
        dark_canvas = _safe_square_canvas(image, padding, "#000000")
        with io.BytesIO() as buf:
            dark_canvas.resize((32, 32), Image.LANCZOS).save(buf, format="PNG")
            zip_file.writestr("favicon-dark-32x32.png", buf.getvalue())

        # OG letterbox (no distortion)
        og_canvas = Image.new("RGBA", (1200, 630), brand_color)
        thumb = canvas.copy()
        thumb.thumbnail((630, 630), Image.LANCZOS)

        x = (1200 - thumb.width) // 2
        y = (630 - thumb.height) // 2

        og_canvas.paste(thumb, (x, y), thumb)

        with io.BytesIO() as buf:
            og_canvas.save(buf, format="PNG")
            zip_file.writestr("social-preview-1200x630.png", buf.getvalue())

        # Manifest
        bg_color = background if background != "transparent" else brand_color
        zip_file.writestr("site.webmanifest", _generate_manifest(brand_color, bg_color))

        # HTML
        zip_file.writestr("favicon-html-code.txt", _generate_html(extension))

    zip_buffer.seek(0)
    return zip_buffer


# ------------------------------------------------
# Main Service
# ------------------------------------------------

async def generate_favicon_service(file, extension, background, padding):

    if extension.lower() not in ALLOWED_OUTPUT_EXT:
        extension = "ico"

    def process():

        with Image.open(file) as image:

            image = ImageOps.exif_transpose(image)
            validate_image_safety(image)
            image = image.convert("RGBA")

            # Smart upscale protection
            if min(image.size) < 256:
                raise HTTPException(
                    status_code=400,
                    detail="Image too small. Minimum recommended size is 256x256."
                )

            image = _trim_transparency(image)

            brand_color = _detect_brand_color(image)

            canvas = _safe_square_canvas(image, padding, background)

            return _build_zip(
                canvas,
                image,
                extension,
                padding,
                background,
                brand_color
            )

    zip_buffer = await run_in_threadpool(process)

    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": "attachment; filename=favicon-package.zip"
        }
    )