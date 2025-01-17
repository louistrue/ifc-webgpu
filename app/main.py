from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from .middleware.api_key import api_key_middleware
from .core import analytics

app = FastAPI(
    title="IFC Service API",
    description="REST API for processing IFC files",
    version="0.0.2",
    openapi_version="3.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add middleware
app.middleware("http")(api_key_middleware)

# Force PostHog initialization
print("Initializing analytics...")
if analytics.posthog is None:
    print("Failed to initialize PostHog!")
else:
    print("PostHog initialized successfully")

# Include the router
app.include_router(router, prefix="/api")