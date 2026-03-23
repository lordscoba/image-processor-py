import io
import os
import tempfile
import asyncio
import time

from PIL import Image
from fastapi.responses import StreamingResponse, FileResponse
from starlette.concurrency import run_in_threadpool
from fastapi import HTTPException, BackgroundTasks

from app.core.logging import logger
from app.utils.profiler import profile_performance

# Constants
MAX_DURATION = 6
STICKER_SIZE = 512
TARGET_SIZE = 512 * 1024
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB Safety Limit

# Concurrency limiting for CPU-heavy FFmpeg tasks
FFMPEG_SEMAPHORE = asyncio.Semaphore(2)

QUALITY_PRESETS = {
    "hd": [
        (15, 80, 512),
        (12, 75, 512),
        (10, 70, 512)
    ],
    "high": [
        (12, 75, 512),
        (10, 70, 512),
        (10, 65, 480)
    ],
    "medium": [
        (10, 65, 480),
        (8, 60, 420)
    ],
    "low": [
        (8, 55, 420),
        (6, 50, 360)
    ]
}


async def run_ffmpeg_async(input_path, output_path, fps, quality, scale, start_time, duration, reverse):
    filters = (
        f"fps={fps},"
        f"scale={scale}:{scale}:force_original_aspect_ratio=decrease,"
        f"pad={STICKER_SIZE}:{STICKER_SIZE}:(ow-iw)/2:(oh-ih)/2:color=0x00000000"
    )

    if reverse:
        filters += ",reverse"

    command = [
        "ffmpeg",
        "-y",
        "-loglevel", "error",
        "-ss", str(start_time),
        "-t", str(duration),
        "-i", input_path,
        "-vf", filters,
        "-an",
        "-vcodec", "libwebp",
        "-preset", "picture",  # Faster WebP preset optimization
        "-qscale", str(quality),
        "-loop", "0",
        output_path
    ]

    # Run natively in the async event loop without blocking threads
    process = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.PIPE
    )
    
    _, stderr = await process.communicate()
    
    if process.returncode != 0:
        raise Exception(f"FFmpeg failed: {stderr.decode()}")


async def adaptive_sticker_encode_async(input_path, start_time, duration, quality, reverse, file_size):
    attempts = QUALITY_PRESETS.get(quality, QUALITY_PRESETS["medium"])

    # Early-exit heuristic: Skip high-quality attempts if the source file is massive
    if file_size > 5 * 1024 * 1024:  # If > 5MB
        attempts = QUALITY_PRESETS["low"]
    elif file_size > 2 * 1024 * 1024: # If > 2MB
        attempts = QUALITY_PRESETS["medium"]

    # Avoid multiple ffmpeg runs for short durations to save CPU
    if duration < 2:
        attempts = attempts[:1]

    best_output = None
    best_size = float("inf")

    for fps, quality_value, scale in attempts:
        fd, output_path = tempfile.mkstemp(suffix=".webp")
        os.close(fd)

        try:
            await run_ffmpeg_async(
                input_path,
                output_path,
                fps,
                quality_value,
                scale,
                start_time,
                duration,
                reverse
            )

            size = os.path.getsize(output_path)

            if size < best_size:
                if best_output and os.path.exists(best_output):
                    os.remove(best_output)
                best_output = output_path
                best_size = size
            else:
                os.remove(output_path)

            if size <= TARGET_SIZE:
                logger.info(f"Sticker target size reached: {size} bytes")
                return best_output

        except Exception as e:
            if os.path.exists(output_path):
                os.remove(output_path)
            raise e

    logger.warning(
        f"Sticker target not reached. Returning best result ({best_size} bytes)."
    )

    return best_output


async def process_video_to_sticker_async(
    input_path: str,
    file_size: int,
    fps: int,
    start_time: float,
    end_time: float,
    quality: str,
    reverse: bool
):
    start_process = time.perf_counter()
    duration = min(end_time - start_time, MAX_DURATION)

    output_path = await adaptive_sticker_encode_async(
        input_path,
        start_time,
        duration,
        quality,
        reverse,
        file_size
    )

    processing_time_ms = int((time.perf_counter() - start_process) * 1000)

    return output_path, file_size, processing_time_ms

@profile_performance
async def video_to_sticker_service(
    file,
    fps: int,
    start_time: float,
    end_time: float,
    quality: str,
    reverse: bool
):
    input_path = None
    output_path = None

    try:
        await file.seek(0)
        file_size = 0
        
        # Safe Chunk Streaming - avoids eating up RAM
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
            while chunk := await file.read(1024 * 1024):  # 1MB chunks
                file_size += len(chunk)
                if file_size > MAX_FILE_SIZE:
                    os.remove(tmp.name)
                    raise HTTPException(status_code=400, detail="Video file too large (max 20MB)")
                tmp.write(chunk)
            input_path = tmp.name

        # Native async concurrency limit (no threadpool needed anymore!)
        async with FFMPEG_SEMAPHORE:
            output_path, original_size, processing_time_ms = await process_video_to_sticker_async(
                input_path,
                file_size,
                fps,
                start_time,
                end_time,
                quality,
                reverse
            )

        filename_base = os.path.splitext(file.filename)[0]

        # Cleanup Task: Runs asynchronously after streaming the FileResponse
        def cleanup_files():
            if output_path and os.path.exists(output_path):
                os.remove(output_path)

        bg_tasks = BackgroundTasks()
        bg_tasks.add_task(cleanup_files)

        # Switched to FileResponse for optimal async non-blocking file serving
        return {
            "response": FileResponse(
                path=output_path,
                media_type="image/webp",
                filename=f"{filename_base}.webp",
                background=bg_tasks
            ),
            "original_size": original_size,
            "processing_time_ms": processing_time_ms
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Video to sticker service error: {str(e)}")
        if output_path and os.path.exists(output_path):
            os.remove(output_path)
        raise HTTPException(status_code=500, detail="Error converting video to sticker")
    finally:
        # Ensures input temp file is deleted even if process crashes
        if input_path and os.path.exists(input_path):
            os.remove(input_path)


def _sync_image_to_sticker(file_obj, file_size: int):
    start_time = time.perf_counter()

    try:
        # Pass FastAPI's SpooledTemporaryFile directly to Pillow (Zero-copy RAM)
        img = Image.open(file_obj)
        
        if img.mode != "RGBA":
            img = img.convert("RGBA")

        img.thumbnail((STICKER_SIZE, STICKER_SIZE), Image.BILINEAR)

        canvas = Image.new("RGBA", (STICKER_SIZE, STICKER_SIZE), (0, 0, 0, 0))

        x = (STICKER_SIZE - img.width) // 2
        y = (STICKER_SIZE - img.height) // 2
        canvas.paste(img, (x, y), img)

        output_buffer = io.BytesIO()

        # Adaptive WebP encoding method based on byte size
        method_val = 4 if file_size < 500_000 else 6

        canvas.save(
            output_buffer,
            format="WEBP",
            quality=80,
            method=method_val
        )

        output_buffer.seek(0)
        processing_time_ms = int((time.perf_counter() - start_time) * 1000)

        return output_buffer, file_size, processing_time_ms

    except Exception as e:
        logger.error(f"Image to sticker sync error: {str(e)}")
        raise e


@profile_performance
async def image_to_sticker_service(file):
    try:
        # 1. Reset pointer just in case
        await file.seek(0)
        
        # 2. Read the bytes directly
        image_bytes = await file.read()
        file_size = len(image_bytes)
        
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="Image file too large (max 20MB)")

        # Run Pillow processing in threadpool, passing the file object directly
        output_buffer, original_size, processing_time_ms = await run_in_threadpool(
            _sync_image_to_sticker,
            file.file,
            file_size
        )

        filename_base = os.path.splitext(file.filename)[0]

        # StreamingResponse is still correct here because output_buffer is in RAM (BytesIO), not a file on disk
        return {
            "response": StreamingResponse(
                output_buffer,
                media_type="image/webp",
                headers={
                    "Content-Disposition": f"attachment; filename={filename_base}.webp"
                }
            ),
            "original_size": original_size,
            "processing_time_ms": processing_time_ms
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Image to sticker wrapper error: {str(e)}")
        raise HTTPException(status_code=500, detail="Error converting image to sticker")