from fastapi import Request
from fastapi.responses import JSONResponse
import os
from dotenv import load_dotenv
import logging
from starlette.status import HTTP_401_UNAUTHORIZED
from ..core.analytics import capture_pageview
import uuid

# Load environment variables
load_dotenv()
logger = logging.getLogger(__name__)

# Get API keys from environment
API_USER_KEYS = os.getenv("API_USER_KEYS", "[]")
if isinstance(API_USER_KEYS, str):
    import json
    try:
        API_USER_KEYS = json.loads(API_USER_KEYS)
    except json.JSONDecodeError:
        API_USER_KEYS = []

async def api_key_middleware(request: Request, call_next):
    # Generate a unique ID for anonymous users
    distinct_id = str(uuid.uuid4())
    
    # Get API key for tracking
    api_key = request.headers.get("X-API-Key", "anonymous")
    
    # Capture pageview with more context
    capture_pageview(
        distinct_id=distinct_id,
        url=str(request.url),
        properties={
            'path': request.url.path,
            'method': request.method,
            'api_key': api_key[:8] if api_key != "anonymous" else "anonymous",  # First 8 chars only for security
            'has_api_key': api_key != "anonymous",
            'referer': request.headers.get("referer", "none")
        }
    )
    
    # List of paths that don't require authentication
    public_paths = [
        "/docs",
        "/redoc", 
        "/openapi.json",
        "/favicon.ico",
        "/docs/oauth2-redirect",
        "/docs/swagger-ui-bundle.js",
        "/docs/swagger-ui.css",
        "/docs/swagger-ui-standalone-preset.js"
    ]
    
    # Get the full path including prefix
    full_path = request.url.path
    
    # Get the referer header
    referer = request.headers.get("referer", "")
    
    # Allow access to Swagger UI and related paths, or if request comes from Swagger UI
    if any(full_path.endswith(path) for path in public_paths) or "/docs" in referer:
        return await call_next(request)
    
    # For all other paths, require API key
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        return JSONResponse(
            status_code=HTTP_401_UNAUTHORIZED,
            content={"detail": "Invalid or missing API Key"}
        )
        
    # Validate API key
    if api_key not in API_USER_KEYS:
        return JSONResponse(
            status_code=HTTP_401_UNAUTHORIZED,
            content={"detail": "Invalid or missing API Key"}
        )
    
    # Process the request if API key is valid
    return await call_next(request) 