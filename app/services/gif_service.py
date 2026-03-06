import io
import os
import tempfile
import time
import subprocess
from PIL import Image
from fastapi.responses import StreamingResponse
from starlette.concurrency import run_in_threadpool
from fastapi import HTTPException
from app.core.logging import logger


MAX_DURATION = 15
MAX_WIDTH = 600
MAX_FPS = 15

TARGET_SIZE = 1 * 1024 * 1024  # 1MB


QUALITY_PRESETS = {
    "hd": [
        (15, 600, 256),
        (12, 600, 256),
        (10, 600, 128)
    ],
    "high": [
        (12, 600, 256),
        (10, 600, 128)
    ],
    "medium": [
        (10, 480, 128),
        (8, 420, 96)
    ],
    "low": [
        (6, 360, 96),
        (5, 320, 64)
    ]
}


def run_ffmpeg(input_path, output_path, fps, width, colors, start_time, duration, reverse):

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

    subprocess.run(
        command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        check=True
    )


def adaptive_gif_encode(input_path, start_time, duration, quality, reverse):

    attempts = QUALITY_PRESETS.get(quality, QUALITY_PRESETS["medium"])

    best_output = None
    best_size = float("inf")

    for fps, width, colors in attempts:

        fd, output_path = tempfile.mkstemp(suffix=".gif")
        os.close(fd)

        run_ffmpeg(
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

            logger.info(f"Target GIF size reached: {size} bytes")

            return best_output

    logger.warning(
        f"Target size not reached. Returning best result ({best_size} bytes)."
    )

    return best_output


def _sync_video_to_gif(
    video_bytes: bytes,
    fps: int,
    width: int,
    start_time: float,
    end_time: float,
    quality: str,
    reverse: bool
):

    start_process_time = time.perf_counter()

    input_path = None
    output_path = None

    try:

        fps = min(fps, MAX_FPS)
        width = min(width, MAX_WIDTH)

        duration = min(end_time - start_time, MAX_DURATION)

        if duration <= 0:
            raise Exception("Invalid trim duration")

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
            tmp.write(video_bytes)
            input_path = tmp.name

        output_path = adaptive_gif_encode(
            input_path,
            start_time,
            duration,
            quality,
            reverse
        )

        gif_file = open(output_path, "rb")

        processing_time_ms = int((time.perf_counter() - start_process_time) * 1000)

        return gif_file, len(video_bytes), processing_time_ms

    except Exception as e:

        logger.error(f"Video → GIF conversion failed: {str(e)}")
        raise

    finally:

        if input_path and os.path.exists(input_path):
            os.remove(input_path)


async def video_to_gif_service(
    file,
    fps: int,
    width: int,
    start_time: float,
    end_time: float,
    quality: str,
    reverse: bool
):

    try:

        await file.seek(0)
        video_bytes = await file.read()

        gif_file, original_size, processing_time_ms = await run_in_threadpool(
            _sync_video_to_gif,
            video_bytes,
            fps,
            width,
            start_time,
            end_time,
            quality,
            reverse
        )

        filename = file.filename.rsplit(".", 1)[0]

        return {
            "response": StreamingResponse(
                gif_file,
                media_type="image/gif",
                headers={
                    "Content-Disposition": f"attachment; filename={filename}.gif"
                }
            ),
            "original_size": original_size,
            "processing_time_ms": processing_time_ms
        }

    except Exception as e:

        logger.error(f"Video to GIF service error: {str(e)}")

        raise HTTPException(
            status_code=500,
            detail="Error converting video to GIF"
        )
    
def _sync_image_to_gif(image_bytes: bytes, duration: int):

    start_time = time.perf_counter()

    try:
        img = Image.open(io.BytesIO(image_bytes))

        frames = []

        if getattr(img, "is_animated", False):

            for frame in range(img.n_frames):
                img.seek(frame)
                frames.append(img.copy())

        else:
            frames = [img]

        output_buffer = io.BytesIO()

        frames[0].save(
            output_buffer,
            format="GIF",
            save_all=True,
            append_images=frames[1:],
            duration=duration,
            loop=0
        )

        output_buffer.seek(0)

        processing_time_ms = int((time.perf_counter() - start_time) * 1000)

        return output_buffer, len(image_bytes), processing_time_ms

    except Exception as e:
        logger.error(f"Image to GIF sync error: {str(e)}")
        raise e


async def image_to_gif_service(file, duration: int):

    try:
        await file.seek(0)
        image_bytes = await file.read()

        output_buffer, original_size, processing_time_ms = await run_in_threadpool(
            _sync_image_to_gif,
            image_bytes,
            duration
        )

        return {
            "response": StreamingResponse(
                output_buffer,
                media_type="image/gif",
                headers={
                    "Content-Disposition": f"attachment; filename={file.filename.split('.')[0]}.gif"
                }
            ),
            "original_size": original_size,
            "processing_time_ms": processing_time_ms
        }

    except Exception as e:
        logger.error(f"Image to GIF wrapper error: {str(e)}")
        raise HTTPException(status_code=500, detail="Error converting image to GIF")