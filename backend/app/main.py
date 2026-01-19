from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="AI Portal API",
    description="Backend API for AI Portal MVP",
    version="0.1.0"
)

# CORS middleware (gateway handles routing, but useful for local dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/healthz")
async def health_check():
    """Health check endpoint for container orchestration."""
    return {"status": "healthy"}


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "AI Portal API", "version": "0.1.0"}


# TODO: Import and include routers
# from app.auth import router as auth_router
# from app.chat import router as chat_router
# app.include_router(auth_router, prefix="/auth", tags=["auth"])
# app.include_router(chat_router, prefix="/chat", tags=["chat"])
