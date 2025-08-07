import os
from redis import Redis
from functools import lru_cache

@lru_cache()
def get_redis() -> Redis:
    """Return a Redis connection using environment variables.

    The host and port are read from ``REDIS_HOST`` and ``REDIS_PORT``
    variables, defaulting to ``redis`` and ``6379`` respectively.
    """
    host = os.environ.get("REDIS_HOST", "redis")
    port = int(os.environ.get("REDIS_PORT", 6379))
    return Redis(host=host, port=port)
