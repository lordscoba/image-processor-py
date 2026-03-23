import time
import tracemalloc
import functools
import asyncio
from app.core.logging import logger

def profile_performance(func):
    """
    A decorator that logs the execution time and peak memory usage of a function.
    Works with both synchronous and asynchronous functions.
    """
    
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        tracemalloc.start()
        start_time = time.perf_counter()
        
        try:
            # Execute the actual async function
            return await func(*args, **kwargs)
        finally:
            # Calculate and log regardless of success or failure
            current_mem, peak_mem = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            execution_time = time.perf_counter() - start_time
            
            logger.info(f"🚀 [PROFILER] {func.__name__}")
            logger.info(f"⏱️ Time:   {execution_time:.4f} sec")
            logger.info(f"💾 Memory: {peak_mem / (1024 * 1024):.2f} MB")

    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        tracemalloc.start()
        start_time = time.perf_counter()
        
        try:
            # Execute the actual sync function
            return func(*args, **kwargs)
        finally:
            current_mem, peak_mem = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            execution_time = time.perf_counter() - start_time
            
            logger.info(f"🚀 [PROFILER] {func.__name__}")
            logger.info(f"⏱️ Time:   {execution_time:.4f} sec")
            logger.info(f"💾 Memory: {peak_mem / (1024 * 1024):.2f} MB")

    # Route to the correct wrapper based on the function type
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper