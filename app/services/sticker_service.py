import io
import os
import tempfile
import subprocess
import time
from PIL import Image
from fastapi.responses import StreamingResponse
from starlette.concurrency import run_in_threadpool
from fastapi import HTTPException
from app.core.logging import logger


MAX_DURATION = 6
STICKER_SIZE = 512
TARGET_SIZE = 512 * 1024  # 512KB


def run_ffmpeg(input_path, output_path, fps, quality, scale):

    command = [
        "ffmpeg",
        "-y",
        "-loglevel", "error",
        "-t", str(MAX_DURATION),
        "-i", input_path,
        "-vf",
        f"fps={fps},"
        f"scale={scale}:{scale}:force_original_aspect_ratio=decrease,"
        f"pad={STICKER_SIZE}:{STICKER_SIZE}:(ow-iw)/2:(oh-ih)/2:color=0x00000000",
        "-loop", "0",
        "-an",
        "-vcodec", "libwebp",
        "-preset", "default",
        "-qscale", str(quality),
        output_path
    ]

    subprocess.run(
        command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        check=True
    )


def adaptive_sticker_encode(input_path):

    attempts = [
        (15, 75, 512),
        (12, 70, 512),
        (10, 65, 512),
        (10, 60, 480),
        (8, 55, 420),
        (6, 50, 360),
    ]

    best_output = None
    best_size = float("inf")

    for fps, quality, scale in attempts:

        fd, output_path = tempfile.mkstemp(suffix=".webp")
        os.close(fd)

        run_ffmpeg(input_path, output_path, fps, quality, scale)

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

    logger.warning(
        f"Sticker target not reached. Returning best result ({best_size} bytes)."
    )

    return best_output


def _sync_video_to_sticker(video_bytes: bytes, fps: int):

    start_time = time.perf_counter()

    input_path = None
    output_path = None

    try:

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
            tmp.write(video_bytes)
            input_path = tmp.name

        output_path = adaptive_sticker_encode(input_path)

        sticker_file = open(output_path, "rb")

        processing_time_ms = int((time.perf_counter() - start_time) * 1000)

        return sticker_file, len(video_bytes), processing_time_ms

    except Exception as e:

        logger.error(f"Video → Sticker conversion failed: {str(e)}")
        raise

    finally:

        if input_path and os.path.exists(input_path):
            os.remove(input_path)


async def video_to_sticker_service(file, fps: int):

    try:

        await file.seek(0)
        video_bytes = await file.read()

        sticker_file, original_size, processing_time_ms = await run_in_threadpool(
            _sync_video_to_sticker,
            video_bytes,
            fps
        )

        filename = file.filename.rsplit(".", 1)[0]

        return {
            "response": StreamingResponse(
                sticker_file,
                media_type="image/webp",
                headers={
                    "Content-Disposition": f"attachment; filename={filename}.webp"
                }
            ),
            "original_size": original_size,
            "processing_time_ms": processing_time_ms
        }

    except Exception as e:

        logger.error(f"Video to sticker service error: {str(e)}")

        raise HTTPException(
            status_code=500,
            detail="Error converting video to sticker"
        )
# import io
# import os
# import tempfile
# import subprocess
# import time
# from PIL import Image
# from fastapi.responses import StreamingResponse
# from starlette.concurrency import run_in_threadpool
# from fastapi import HTTPException
# from app.core.logging import logger


# STICKER_SIZE = 512


# # VIDEO → STICKER
# def _sync_video_to_sticker(video_bytes: bytes, fps: int):

#     start_time = time.perf_counter()

#     input_path = None
#     output_path = None

#     try:

#         with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
#             tmp.write(video_bytes)
#             input_path = tmp.name

#         output_path = tempfile.mktemp(suffix=".webp")

#         command = [
#             "ffmpeg",
#             "-y",
#             "-t", "6",
#             "-i", input_path,
#             "-vf", f"fps={fps},scale={STICKER_SIZE}:{STICKER_SIZE}:force_original_aspect_ratio=decrease,pad={STICKER_SIZE}:{STICKER_SIZE}:(ow-iw)/2:(oh-ih)/2:color=0x00000000",
#             "-loop", "0",
#             "-an",
#             "-vcodec", "libwebp",
#             "-lossless", "0",
#             "-qscale", "75",
#             "-preset", "default",
#             "-an",
#             output_path
#         ]

#         subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

#         with open(output_path, "rb") as f:
#             sticker_bytes = f.read()

#         output_buffer = io.BytesIO(sticker_bytes)

#         processing_time_ms = int((time.perf_counter() - start_time) * 1000)

#         return output_buffer, len(video_bytes), processing_time_ms

#     except Exception as e:
#         logger.error(f"Video to sticker sync error: {str(e)}")
#         raise e

#     finally:

#         if input_path and os.path.exists(input_path):
#             os.remove(input_path)

#         if output_path and os.path.exists(output_path):
#             os.remove(output_path)



# async def video_to_sticker_service(file, fps: int):

#     try:

#         await file.seek(0)
#         video_bytes = await file.read()

#         output_buffer, original_size, processing_time_ms = await run_in_threadpool(
#             _sync_video_to_sticker,
#             video_bytes,
#             fps
#         )

#         return {
#             "response": StreamingResponse(
#                 output_buffer,
#                 media_type="image/webp",
#                 headers={
#                     "Content-Disposition": f"attachment; filename={file.filename.split('.')[0]}.webp"
#                 }
#             ),
#             "original_size": original_size,
#             "processing_time_ms": processing_time_ms
#         }

#     except Exception as e:
#         logger.error(f"Video to sticker wrapper error: {str(e)}")
#         raise HTTPException(status_code=500, detail="Error converting video to sticker")
    


def _sync_image_to_sticker(image_bytes: bytes):

    start_time = time.perf_counter()

    try:

        img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")

        img.thumbnail((STICKER_SIZE, STICKER_SIZE))

        canvas = Image.new("RGBA", (STICKER_SIZE, STICKER_SIZE), (0, 0, 0, 0))

        x = (STICKER_SIZE - img.width) // 2
        y = (STICKER_SIZE - img.height) // 2

        canvas.paste(img, (x, y), img)

        output_buffer = io.BytesIO()

        canvas.save(
            output_buffer,
            format="WEBP",
            quality=80,
            method=6
        )

        output_buffer.seek(0)

        processing_time_ms = int((time.perf_counter() - start_time) * 1000)

        return output_buffer, len(image_bytes), processing_time_ms

    except Exception as e:
        logger.error(f"Image to sticker sync error: {str(e)}")
        raise e


async def image_to_sticker_service(file):

    try:

        await file.seek(0)
        image_bytes = await file.read()

        output_buffer, original_size, processing_time_ms = await run_in_threadpool(
            _sync_image_to_sticker,
            image_bytes
        )

        return {
            "response": StreamingResponse(
                output_buffer,
                media_type="image/webp",
                headers={
                    "Content-Disposition": f"attachment; filename={file.filename.split('.')[0]}.webp"
                }
            ),
            "original_size": original_size,
            "processing_time_ms": processing_time_ms
        }

    except Exception as e:
        logger.error(f"Image to sticker wrapper error: {str(e)}")
        raise HTTPException(status_code=500, detail="Error converting image to sticker")