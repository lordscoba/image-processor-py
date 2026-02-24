# from rembg import remove
# import io
# from fastapi.responses import StreamingResponse
# from fastapi import HTTPException

# def remove_background(file):
#     try:
#         output = remove(file.read())

#         buffer = io.BytesIO(output)
#         buffer.seek(0)

#         return StreamingResponse(
#             buffer,
#             media_type="image/png",
#             headers={"Content-Disposition": "attachment; filename=background_removed.png"}
#         )
#     except Exception:
#         raise HTTPException(status_code=500, detail="Background removal failed")