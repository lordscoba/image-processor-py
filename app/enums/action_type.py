from enum import Enum

class ActionType(str, Enum):
    CONVERT = "convert"
    OPTIMIZE = "optimize"
    ANALYZE = "analyze"
    SVG_OPTIMIZE = "svg_optimize"
    CROP = "crop"
    RESIZE = "resize"
    TO_BASE64 = "to_base64"
    FROM_BASE64 = "from_base64"
    FAVICON_GENERATE = "favicon_generate"
    OPTIMIZE_TWITTER = "optimize_twitter"
    OPTIMIZE_WHATSAPP = "optimize_whatsapp"
    OPTIMIZE_WEB = "optimize_web"
    OPTIMIZE_CUSTOM = "optimize_custom"
    OPTIMIZE_INSTAGRAM = "optimize_instagram"
    OPTIMIZE_YOUTUBE = "optimize_youtube"
    OPTIMIZE_SEO = "optimize_seo"


    PDF_COMPRESS = "pdf_compress"
    PDF_COMPRESS_PRO = "pdf_compress_pro"

    IMAGE_TO_PDF = "image_to_pdf"
    PDF_TO_IMAGE = "pdf_to_image"

    EXIF_SCRUBBER = "exif_scrubber"

    HEIC_TO_IMAGE = "heic_to_image"
    IMAGE_TO_HEIC = "image_to_heic"

    IMAGE_COLOR_EFFECTS = "image_color_effects"
    IMAGE_DPI_CHANGER = "image_dpi_changer"
    IMAGE_DPI_CHECKER = "image_dpi_checker"
    
    PASSWORD_GENERATOR = "password_generator"
    EXTRACT_PDF_IMAGES = "extract_pdf_images"
    VIDEO_TO_STICKER = "video_to_sticker"
    IMAGE_TO_STICKER = "image_to_sticker"
    VIDEO_TO_GIF = "video_to_gif"
    IMAGE_TO_GIF = "image_to_gif"
    WATERMARK_IMAGES = "watermark_images"

