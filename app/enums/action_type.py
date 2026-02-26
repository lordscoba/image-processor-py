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