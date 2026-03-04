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


def run_ffmpeg(input_path, output_path, fps, width, colors):

    command = [
        "ffmpeg",
        "-y",
        "-loglevel", "error",
        "-t", str(MAX_DURATION),
        "-i", input_path,
        "-vf",
        f"fps={fps},scale={width}:-1:flags=lanczos,mpdecimate,"
        f"split[s0][s1];[s0]palettegen=max_colors={colors}[p];"
        f"[s1][p]paletteuse=dither=bayer:bayer_scale=3",
        "-loop", "0",
        output_path
    ]

    subprocess.run(
        command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        check=True
    )


def adaptive_gif_encode(input_path):

    attempts = [
        (12, 600, 256),
        (10, 600, 128),
        (8, 480, 128),
        (6, 420, 96),
        (5, 360, 64)
    ]

    best_output = None
    best_size = float("inf")

    for fps, width, colors in attempts:

        fd, output_path = tempfile.mkstemp(suffix=".gif")
        os.close(fd)

        run_ffmpeg(input_path, output_path, fps, width, colors)

        size = os.path.getsize(output_path)

        # Track the smallest GIF produced
        if size < best_size:
            if best_output and os.path.exists(best_output):
                os.remove(best_output)

            best_output = output_path
            best_size = size
        else:
            os.remove(output_path)

        # If we reach target size, stop early
        if size <= TARGET_SIZE:
            logger.info(f"Target GIF size reached: {size} bytes")
            return best_output

    logger.warning(
        f"Target size not reached. Returning best result ({best_size} bytes)."
    )

    return best_output


def _sync_video_to_gif(video_bytes: bytes, fps: int, width: int):

    start_time = time.perf_counter()

    input_path = None
    output_path = None

    try:

        fps = min(fps, MAX_FPS)
        width = min(width, MAX_WIDTH)

        # write uploaded video
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
            tmp.write(video_bytes)
            input_path = tmp.name

        # adaptive compression
        output_path = adaptive_gif_encode(input_path)

        gif_file = open(output_path, "rb")

        processing_time_ms = int((time.perf_counter() - start_time) * 1000)

        return gif_file, len(video_bytes), processing_time_ms

    except Exception as e:

        logger.error(f"Video → GIF conversion failed: {str(e)}")
        raise

    finally:

        if input_path and os.path.exists(input_path):
            os.remove(input_path)


async def video_to_gif_service(file, fps: int, width: int):

    try:

        await file.seek(0)
        video_bytes = await file.read()

        gif_file, original_size, processing_time_ms = await run_in_threadpool(
            _sync_video_to_gif,
            video_bytes,
            fps,
            width
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


# def _sync_video_to_gif(video_bytes: bytes, fps: int, width: int):

#     start_time = time.perf_counter()

#     input_path = None
#     output_path = None

#     try:

#         fps = min(fps, MAX_FPS)
#         width = min(width, MAX_WIDTH)

#         # write video
#         with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
#             tmp.write(video_bytes)
#             input_path = tmp.name

#         output_path = tempfile.mktemp(suffix=".gif")

#         command = [
#             "ffmpeg",
#             "-y",
#             "-t", str(MAX_DURATION),   # auto trim
#             "-i", input_path,
#             "-vf", f"fps={fps},scale={width}:-1:flags=lanczos",
#             "-loop", "0",
#             output_path
#         ]

#         subprocess.run(
#             command,
#             stdout=subprocess.PIPE,
#             stderr=subprocess.PIPE,
#             check=True
#         )

#         with open(output_path, "rb") as f:
#             gif_bytes = f.read()

#         output_buffer = io.BytesIO(gif_bytes)

#         processing_time_ms = int((time.perf_counter() - start_time) * 1000)

#         return output_buffer, len(video_bytes), processing_time_ms

#     except Exception as e:
#         logger.error(f"FFmpeg GIF error: {str(e)}")
#         raise e

#     finally:

#         if input_path and os.path.exists(input_path):
#             os.remove(input_path)

#         if output_path and os.path.exists(output_path):
#             os.remove(output_path)


# async def video_to_gif_service(file, fps: int, width: int):

#     try:

#         await file.seek(0)
#         video_bytes = await file.read()

#         output_buffer, original_size, processing_time_ms = await run_in_threadpool(
#             _sync_video_to_gif,
#             video_bytes,
#             fps,
#             width
#         )

#         return {
#             "response": StreamingResponse(
#                 output_buffer,
#                 media_type="image/gif",
#                 headers={
#                     "Content-Disposition": f"attachment; filename={file.filename.split('.')[0]}.gif"
#                 }
#             ),
#             "original_size": original_size,
#             "processing_time_ms": processing_time_ms
#         }

#     except Exception as e:
#         logger.error(f"Video to GIF wrapper error: {str(e)}")
#         raise HTTPException(status_code=500, detail="Error converting video to GIF")
    
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