import io
from fastapi.concurrency import run_in_threadpool
from scour import scour

def _run_scour(svg_text: str):
    """Synchronous CPU-bound task."""
    options = scour.sanitizeOptions()
    options.digits = 3 # Better balance of size vs quality
    options.remove_metadata = True
    options.strip_comments = True
    options.enable_viewboxing = True
    options.shorten_ids = True
    options.indent_type = None
    options.newlines = False
    options.strip_xml_prolog = True # Saves more space
    
    return scour.scourString(svg_text, options)

async def optimize_svg_service(svg_content: str):
    # Offload the heavy lifting to a thread so FastAPI stays responsive
    optimized_svg = await run_in_threadpool(_run_scour, svg_content)
    
    buffer = io.BytesIO(optimized_svg.encode("utf-8"))
    return buffer