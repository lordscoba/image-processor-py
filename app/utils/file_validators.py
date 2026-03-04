from fastapi import UploadFile, HTTPException
from app.core.config import MAX_FILE_SIZE, ALLOWED_EXTENSIONS, MAX_FILE_SIZE_VIDEO


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