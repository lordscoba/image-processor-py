import io
import os
import tempfile
import asyncio
import time

from PIL import Image
from fastapi.responses import StreamingResponse, FileResponse
from fastapi import HTTPException, BackgroundTasks
from app.core.logging import logger
from app.utils.profiler import profile_performance
from starlette.concurrency import run_in_threadpool

# ─────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────
MAX_DURATION = 15
MAX_WIDTH = 600
MAX_FPS = 15
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB

TARGET_SIZE = 1 * 1024 * 1024  # 1MB

FFMPEG_SEMAPHORE = asyncio.Semaphore(2)

QUALITY_PRESETS = {
    "hd": [(15, 600, 256), (12, 600, 256), (10, 600, 128)],
    "high": [(12, 600, 256), (10, 600, 128)],
    "medium": [(10, 480, 128), (8, 420, 96)],
    "low": [(6, 360, 96), (5, 320, 64)]
}

# ─────────────────────────────────────────────
# ASYNC FFMPEG
# ─────────────────────────────────────────────
async def run_ffmpeg_async(input_path, output_path, fps, width, colors, start_time, duration, reverse):
    filters = f"fps={fps},scale={width}:-1:flags=lanczos"

    if reverse:
        filters += ",reverse"

    filters += (
        f",split[s0][s1];"
        f"[s0]palettegen=max_colors={colors}[p];"
        f"[s1][p]paletteuse=dither=bayer:bayer_scale=3"
    )

    command = [
        "ffmpeg",
        "-y",
        "-loglevel", "error",
        "-ss", str(start_time),
        "-t", str(duration),
        "-i", input_path,
        "-vf", filters,
        "-loop", "0",
        output_path
    ]

    process = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.PIPE
    )

    _, stderr = await process.communicate()

    if process.returncode != 0:
        raise Exception(f"FFmpeg failed: {stderr.decode()}")


# ─────────────────────────────────────────────
# ADAPTIVE ENCODER
# ─────────────────────────────────────────────
async def adaptive_gif_encode_async(input_path, start_time, duration, quality, reverse, file_size):
    attempts = QUALITY_PRESETS.get(quality, QUALITY_PRESETS["medium"])

    # Reduce quality attempts for large files
    if file_size > 5 * 1024 * 1024:
        attempts = QUALITY_PRESETS["low"]
    elif file_size > 2 * 1024 * 1024:
        attempts = QUALITY_PRESETS["medium"]

    # Avoid multiple passes for short clips
    if duration < 2:
        attempts = attempts[:1]

    best_output = None
    best_size = float("inf")

    for fps, width, colors in attempts:
        fd, output_path = tempfile.mkstemp(suffix=".gif")
        os.close(fd)

        try:
            await run_ffmpeg_async(
                input_path,
                output_path,
                fps,
                width,
                colors,
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
                logger.info(f"Target GIF size reached: {size}")
                return best_output

        except Exception as e:
            if os.path.exists(output_path):
                os.remove(output_path)
            raise e

    return best_output


# ─────────────────────────────────────────────
# VIDEO → GIF
# ─────────────────────────────────────────────
async def process_video_to_gif_async(
    input_path,
    file_size,
    fps,
    width,
    start_time,
    end_time,
    quality,
    reverse
):
    start = time.perf_counter()

    fps = min(fps, MAX_FPS)
    width = min(width, MAX_WIDTH)

    duration = min(end_time - start_time, MAX_DURATION)

    if duration <= 0:
        raise Exception("Invalid duration")

    output_path = await adaptive_gif_encode_async(
        input_path,
        start_time,
        duration,
        quality,
        reverse,
        file_size
    )

    processing_time = int((time.perf_counter() - start) * 1000)

    return output_path, file_size, processing_time


@profile_performance
async def video_to_gif_service(
    file,
    fps: int,
    width: int,
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

        # STREAM FILE (NO MEMORY LOAD)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
            while chunk := await file.read(1024 * 1024):
                file_size += len(chunk)

                if file_size > MAX_FILE_SIZE:
                    os.remove(tmp.name)
                    raise HTTPException(status_code=400, detail="File too large")

                tmp.write(chunk)

            input_path = tmp.name

        async with FFMPEG_SEMAPHORE:
            output_path, original_size, processing_time_ms = await process_video_to_gif_async(
                input_path,
                file_size,
                fps,
                width,
                start_time,
                end_time,
                quality,
                reverse
            )

        filename = os.path.splitext(file.filename)[0]

        def cleanup():
            if output_path and os.path.exists(output_path):
                os.remove(output_path)

        bg = BackgroundTasks()
        bg.add_task(cleanup)

        return {
            "response": FileResponse(
                path=output_path,
                media_type="image/gif",
                filename=f"{filename}.gif",
                background=bg
            ),
            "original_size": original_size,
            "processing_time_ms": processing_time_ms
        }

    except Exception as e:
        logger.error(f"Video → GIF error: {e}")

        if output_path and os.path.exists(output_path):
            os.remove(output_path)

        raise HTTPException(status_code=500, detail="GIF conversion failed")

    finally:
        if input_path and os.path.exists(input_path):
            os.remove(input_path)


# ─────────────────────────────────────────────
# IMAGE → GIF
# ─────────────────────────────────────────────
def _sync_image_to_gif(file_obj, file_size, duration):
    start = time.perf_counter()

    try:
        file_obj.seek(0)

        img = Image.open(file_obj)

        frames = []

        if getattr(img, "is_animated", False):
            for i in range(img.n_frames):
                img.seek(i)
                frames.append(img.copy())
        else:
            frames = [img]

        output = io.BytesIO()

        frames[0].save(
            output,
            format="GIF",
            save_all=True,
            append_images=frames[1:],
            duration=duration,
            loop=0
        )

        output.seek(0)

        return output, file_size, int((time.perf_counter() - start) * 1000)

    except Exception as e:
        logger.error(f"Image → GIF sync error: {e}")
        raise e


@profile_performance
async def image_to_gif_service(file, duration: int):
    try:
        await file.seek(0)

        content = await file.read()
        file_size = len(content)

        if file_size > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="Image too large")

        output, size, time_ms = await run_in_threadpool(
            _sync_image_to_gif,
            file.file,
            file_size,
            duration
        )

        filename = os.path.splitext(file.filename)[0]

        return {
            "response": StreamingResponse(
                output,
                media_type="image/gif",
                headers={
                    "Content-Disposition": f'attachment; filename="{filename}.gif"'
                }
            ),
            "original_size": size,
            "processing_time_ms": time_ms
        }

    except Exception as e:
        logger.error(f"Image → GIF error: {e}")
        raise HTTPException(status_code=500, detail="GIF conversion failed")