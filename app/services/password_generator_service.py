import time
import secrets
import string
from starlette.concurrency import run_in_threadpool
from fastapi import HTTPException
from app.core.logging import logger


def _sync_generate_password(length, uppercase, lowercase, numbers, symbols, exclude_chars):

    start_time = time.perf_counter()

    try:

        char_pool = ""
        required_chars = []

        upper_chars = string.ascii_uppercase
        lower_chars = string.ascii_lowercase
        number_chars = string.digits
        symbol_chars = string.punctuation

        # Normalize excluded characters safely
        excluded_set = set(exclude_chars) if exclude_chars else set()

        # Apply exclusions
        upper_chars = "".join(c for c in upper_chars if c not in excluded_set)
        lower_chars = "".join(c for c in lower_chars if c not in excluded_set)
        number_chars = "".join(c for c in number_chars if c not in excluded_set)
        symbol_chars = "".join(c for c in symbol_chars if c not in excluded_set)

        # Ensure at least one char from each selected set
        if uppercase and upper_chars:
            required_chars.append(secrets.choice(upper_chars))
            char_pool += upper_chars

        if lowercase and lower_chars:
            required_chars.append(secrets.choice(lower_chars))
            char_pool += lower_chars

        if numbers and number_chars:
            required_chars.append(secrets.choice(number_chars))
            char_pool += number_chars

        if symbols and symbol_chars:
            required_chars.append(secrets.choice(symbol_chars))
            char_pool += symbol_chars

        if not char_pool:
            raise ValueError("No characters available after exclusions")

        if length < len(required_chars):
            raise ValueError("Password length too small for selected character sets")

        remaining_length = length - len(required_chars)

        random_chars = [
            secrets.choice(char_pool)
            for _ in range(remaining_length)
        ]

        password_list = required_chars + random_chars

        # Secure shuffle
        secrets.SystemRandom().shuffle(password_list)

        password = "".join(password_list)

        processing_time_ms = int((time.perf_counter() - start_time) * 1000)

        return {
            "password": password,
            "length": length,
            "excluded_characters": "".join(excluded_set),
            "processing_time_ms": processing_time_ms
        }

    except Exception as e:
        logger.error(f"Password generation sync error: {str(e)}")
        raise e


async def password_generator_service(
    length: int,
    uppercase: bool,
    lowercase: bool,
    numbers: bool,
    symbols: bool,
    exclude_chars: str
):

    try:

        result = await run_in_threadpool(
            _sync_generate_password,
            length,
            uppercase,
            lowercase,
            numbers,
            symbols,
            exclude_chars
        )

        return result

    except Exception as e:
        logger.error(f"Password generator wrapper error: {str(e)}")
        raise HTTPException(status_code=500, detail="Error generating password.")