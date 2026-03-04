import os
import tempfile
from typing import Any, Dict, Union

from PIL import Image, ImageStat, ExifTags
import io
import numpy as np
from fastapi import HTTPException
import exiftool

def get_hex_color(rgb):
    return '#%02x%02x%02x' % rgb

def get_color_palette(image, num_colors=5):
    """Extracts a palette of the most frequent colors."""
    small = image.resize((100, 100))
    result = small.convert("RGB").getcolors(10000)
    # Sort by frequency and take the top N
    sorted_colors = sorted(result, key=lambda x: x[0], reverse=True)
    return [
        {"rgb": c[1], "hex": get_hex_color(c[1]), "frequency": c[0]} 
        for c in sorted_colors[:num_colors]
    ]
# def get_image_metadata(image_source: Union[str, Image.Image]) -> Dict[str, Any]:
#     metadata: Dict[str, Any] = {}
#     temp_path = None

#     try:
#         # 1. Handle Input Source (Same as before, but keeping original format)
#         if not isinstance(image_source, (str, os.PathLike)):
#             fmt = getattr(image_source, 'format', 'JPEG')
#             with tempfile.NamedTemporaryFile(delete=False, suffix=f".{fmt.lower()}") as tmp:
#                 image_source.save(tmp.name, format=fmt)
#                 temp_path = tmp.name
#                 image_path = temp_path
#         else:
#             image_path = image_source

#         # ---------- Extract metadata using ExifTool ----------
#         with exiftool.ExifToolHelper() as et:
#             # We fetch all tags to ensure we don't miss Creator/GPS
#             data = et.get_metadata(image_path)
            
#         if data:
#             raw = data[0]
            
#             # --- Capture Specific High-Value Fields ---
#             # Date Created (Checks common variations)
#             metadata["date_created"] = raw.get("EXIF:DateTimeOriginal") or \
#                                       raw.get("XMP:CreateDate") or \
#                                       raw.get("IPTC:DateCreated")
            
#             # Creator / Author
#             metadata["creator"] = raw.get("EXIF:Artist") or \
#                                  raw.get("XMP:Creator") or \
#                                  raw.get("IPTC:By-line") or \
#                                  raw.get("Creator")
            
#             # GPS Data (ExifTool merges these into convenient 'Composite' tags)
#             metadata["gps_latitude"] = raw.get("Composite:GPSLatitude")
#             metadata["gps_longitude"] = raw.get("Composite:GPSLongitude")
#             metadata["gps_altitude"] = raw.get("Composite:GPSAltitude")
            
#             # Add a Google Maps link if GPS exists
#             if metadata["gps_latitude"] and metadata["gps_longitude"]:
#                 metadata["google_maps_link"] = f"https://www.google.com/maps?q={metadata['gps_latitude']},{metadata['gps_longitude']}"

#             # --- Capture Everything Else (Flattened) ---
#             for key, value in raw.items():
#                 if isinstance(value, (bytes, bytearray)):
#                     continue
                
#                 # We prefix the key with its source to prevent overwriting
#                 # e.g., 'EXIF_Model', 'XMP_Creator'
#                 safe_key = key.replace(":", "_")
#                 metadata[safe_key] = str(value)

#         # ---------- Pillow Layer (Visual attributes) ----------
#         with Image.open(image_path) as img:
#             metadata["dimensions"] = f"{img.width}x{img.height}"
#             metadata["color_mode"] = img.mode
#             metadata["format"] = img.format

#     except Exception as e:
#         metadata["error"] = str(e)
#     finally:
#         if temp_path and os.path.exists(temp_path):
#             os.remove(temp_path)

#     return metadata

# def get_image_metadata(image_source: Union[str, Image.Image]) -> Dict[str, Any]:
#     metadata: Dict[str, Any] = {}
#     temp_path = None

#     try:
#     # 1. Handle PIL Image objects by saving to a temp file
#         if not isinstance(image_source, (str, os.PathLike)):
#             with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
#                 # FIX: Check if image has transparency (RGBA or LA) and convert to RGB
#                 if image_source.mode in ("RGBA", "P", "LA"):
#                     # Create a white background to paste the transparent image onto
#                     bg = Image.new("RGB", image_source.size, (255, 255, 255))
#                     # If mode is 'P' (palette), convert to RGBA first to get the mask
#                     img_rgba = image_source.convert("RGBA")
#                     bg.paste(img_rgba, mask=img_rgba.split()[3]) # 3 is the alpha channel
#                     bg.save(tmp.name, format="JPEG")
#                 else:
#                     # If it's already RGB or L, just save normally
#                     image_source.save(tmp.name, format="JPEG")
                
#                 temp_path = tmp.name
#                 image_path = temp_path
#         else:
#             image_path = image_source

#         # 2. Safety check for path existence
#         if not os.path.exists(image_path):
#             return {"error": "File path not found"}

#         # ---------- Extract metadata using ExifTool ----------
#         try:
#             with exiftool.ExifToolHelper() as et:
#                 data = et.get_metadata(image_path)
                
#             if data:
#                 raw = data[0]
#                 for key, value in raw.items():
#                     if isinstance(value, (bytes, bytearray)):
#                         continue
#                     clean_key = key.split(":")[-1]
#                     metadata[clean_key] = str(value)
#         except Exception as e:
#             metadata["exiftool_error"] = str(e)

#         # ---------- Additional checks using Pillow ----------
#         # We use the original source if it's already an Image object to save memory
#         try:
#             img = image_source if not isinstance(image_source, str) else Image.open(image_path)
            
#             if img.info.get("icc_profile"):
#                 metadata["Has_ICC_Profile"] = "True"

#             exif_data = img.getexif()
#             if exif_data and (0x014a in exif_data or 0x501B in exif_data):
#                 metadata["Has_Thumbnail"] = "True"
                
#             metadata["Format"] = getattr(img, 'format', 'Unknown')
#             metadata["Size"] = f"{img.width}x{img.height}"
            
#             # Close the image if we opened it locally
#             if isinstance(image_source, str):
#                 img.close()

#         except Exception as e:
#             metadata["pillow_error"] = str(e)

#     finally:
#         # 3. CLEANUP: Delete the temp file if we created one
#         if temp_path and os.path.exists(temp_path):
#             os.remove(temp_path)

#     return metadata
def get_image_metadata(image):
    """Extracts Exif data and converts it into a readable dictionary."""
    metadata = {}
    info = image.getexif()
    if info:
        for tag, value in info.items():
            decoded = ExifTags.TAGS.get(tag, tag)
            # Filter out bulky byte data (like thumbnails) for a clean JSON response
            if isinstance(value, bytes):
                continue
            metadata[decoded] = str(value)
    return metadata

def calculate_visual_metrics(image):
    """Calculates brightness and perceived contrast."""
    stat = ImageStat.Stat(image.convert("L")) # Convert to grayscale for metrics
    brightness = stat.mean[0]
    contrast = stat.stddev[0] # Standard deviation represents contrast
    return round(brightness, 2), round(contrast, 2)

def analyze_image(file_bytes: bytes):
    try:
        image = Image.open(io.BytesIO(file_bytes))
        width, height = image.size
        
        # 1. Basic properties
        aspect_ratio = round(width / height, 2)
        size_kb = round(len(file_bytes) / 1024, 2)
        
        # 2. Visual Analysis
        palette = get_color_palette(image)
        brightness, contrast = calculate_visual_metrics(image)
        
        # 3. Metadata Extraction
        metadata = get_image_metadata(image)

        # 4. Smart Recommendations
        recommendations = []
        if size_kb > 1500:
            recommendations.append("File size is heavy (over 1.5MB); use compression.")
        if width > 3000 or height > 3000:
            recommendations.append("Ultra-high resolution; consider resizing for standard web use.")
        if image.format not in ["WEBP", "AVIF"]:
            recommendations.append(f"Format is {image.format}; WEBP would reduce size by ~30%.")
        if brightness < 40:
            recommendations.append("Image is very dark; consider increasing exposure.")
        if contrast < 20:
            recommendations.append("Image has low contrast; it may appear washed out.")

        return {
            "basic_info": {
                "width": width,
                "height": height,
                "aspect_ratio": aspect_ratio,
                "format": image.format,
                "mode": image.mode,
                "file_size_kb": size_kb,
            },
            "visual_analysis": {
                "brightness_score": brightness,
                "contrast_score": contrast,
                "primary_color": palette[0],
                "color_palette": palette,
            },
            "metadata": metadata,
            "recommendations": recommendations
        }

    except Exception as e:
        print(f"Analysis Error: {e}")
        raise HTTPException(status_code=400, detail="Could not analyze image.")