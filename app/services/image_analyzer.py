from PIL import Image, ImageStat, ExifTags
import io
import numpy as np
from fastapi import HTTPException

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

def get_image_metadata(image):
    """Extracts Exif data and converts it into a readable dictionary."""
    metadata = {}
    info = image._getexif()
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