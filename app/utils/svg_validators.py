import re
from fastapi import HTTPException

def validate_svg_safety(svg_content: str):

    content = svg_content.lower()

    # 1️⃣ Detect <script> tags
    if re.search(r'<\s*script', content):
        raise HTTPException(
            status_code=400,
            detail="Security Risk Detected: <script> tags are not allowed in SVG files."
        )

    # 2️⃣ Detect javascript: protocol (even encoded versions)
    if re.search(r'javascript\s*:', content):
        raise HTTPException(
            status_code=400,
            detail="Security Risk Detected: 'javascript:' URIs are not allowed in SVG files."
        )

    # 3️⃣ Detect inline event handlers (onload=, onclick=, etc.)
    if re.search(r'on\w+\s*=', content):
        raise HTTPException(
            status_code=400,
            detail="Security Risk Detected: Inline event handlers (e.g., onload, onclick) are not allowed in SVG files."
        )

    # 4️⃣ Detect foreignObject (can embed HTML inside SVG)
    if re.search(r'<\s*foreignobject', content):
        raise HTTPException(
            status_code=400,
            detail="Security Risk Detected: <foreignObject> elements are not allowed in SVG files."
        )

    # 5️⃣ Detect iframe/object/embed
    if re.search(r'<\s*(iframe|object|embed)', content):
        raise HTTPException(
            status_code=400,
            detail="Security Risk Detected: Embedded external content (iframe/object/embed) is not allowed in SVG files."
        )