from functools import lru_cache
import hashlib

def generate_cache_key(content: bytes):
    return hashlib.md5(content).hexdigest()

cache_store = {}