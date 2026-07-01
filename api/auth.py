import os
from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

API_KEY = os.getenv("API_KEY", "dev-secret-change-in-prod")
api_key_scheme = APIKeyHeader(name="X-API-Key", auto_error=True)


def verify_api_key(key: str = Security(api_key_scheme)) -> str:
    """Verifies that the provided API key matches the expected one."""
    if key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return key
