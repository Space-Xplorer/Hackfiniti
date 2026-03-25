import os
import uuid
from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

def _rate_key(request: Request) -> str:
    # Evaluated at request time so TEST_MODE set before/after import works.
    if os.environ.get("TEST_MODE", "").lower() == "true":
        # Unique key per request → shared counter never accumulates → no throttling
        return str(uuid.uuid4())
    return get_remote_address(request)

limiter = Limiter(key_func=_rate_key)
