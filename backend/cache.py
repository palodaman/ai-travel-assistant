import os
import json
import hashlib
import redis

_redis = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))


def cache_get(key: str):
    return _redis.get(key)


def cache_set(key: str, value: dict, ttl=300):
    _redis.setex(key, ttl, json.dumps(value))


def key_for(prefix, payload):
    return (
        prefix
        + ":"
        + hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:24]
    )
