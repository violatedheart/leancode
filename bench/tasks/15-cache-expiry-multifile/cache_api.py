from cache_store import TTLCache


def lookup(cache: TTLCache, key: str, now: float):
    return cache.get(key, now)
