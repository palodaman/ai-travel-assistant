from flask import Flask
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import redis
import os


def harden(app: Flask):
    # CORS is now handled in app.py

    # Configure storage backend for rate limiter
    # Use Redis if available, otherwise use in-memory storage (for development)
    storage_uri = None

    # First check for REDIS_URL (used in Docker Compose)
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        try:
            # Test the connection
            from urllib.parse import urlparse
            parsed = urlparse(redis_url)
            redis_client = redis.Redis(
                host=parsed.hostname or "localhost",
                port=parsed.port or 6379,
                db=int(parsed.path.lstrip("/")) if parsed.path else 0,
                decode_responses=True
            )
            redis_client.ping()
            storage_uri = redis_url
        except:
            storage_uri = "memory://"
    else:
        # Fallback to separate host/port (for local development)
        try:
            redis_host = os.getenv("REDIS_HOST", "localhost")
            redis_port = int(os.getenv("REDIS_PORT", 6379))
            redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
            redis_client.ping()
            storage_uri = f"redis://{redis_host}:{redis_port}"
        except:
            storage_uri = "memory://"

    # Rate limit with configured storage
    Limiter(
        get_remote_address,
        app=app,
        default_limits=["60/minute", "1000/day"],
        storage_uri=storage_uri
    )

    @app.after_request
    def set_headers(resp):
        resp.headers["X-Content-Type-Options"] = "nosniff"
        resp.headers["X-Frame-Options"] = "DENY"
        resp.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        resp.headers["Permissions-Policy"] = "geolocation=(), microphone=()"
        return resp

    return app
