from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.exceptions import register_exception_handlers
from app.core.logging import setup_logging
from app.api.v1.router import api_router

setup_logging()

app = FastAPI(
    title = "learn english",
    description = "API for learning english",
    version = "1.0.0"
)

register_exception_handlers(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins = ["*"],
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"],
)

app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/health")
async def health():
    return {"status": "ok"}


