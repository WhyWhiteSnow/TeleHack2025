from fastapi import FastAPI
from loguru import logger

from core.config import config
from core.logger import *  # noqa
from middlewares.logging import LoggingMiddleware
from routers.files.router import router as files_router

app = FastAPI(
    title="Document Viewer API",
    description="API for document viewer",
    version=config.VERSION,
    docs_url="/docs",
)

app.add_middleware(LoggingMiddleware)

app.include_router(files_router)


@app.get("/health")
def health():
    return {
        "status": "OK",
        "mode": config.MODE,
        "version": config.VERSION,
        "docs_url": "/docs" if config.MODE == "DEV" else None,
    }


if __name__ == "__main__":
    import uvicorn

    logger.info(f"Starting server in {config.MODE} mode on {config.HOST}:{config.PORT}")
    uvicorn.run(
        "main:app",
        host=config.HOST,
        port=config.PORT,
        reload=True if config.MODE == "DEV" else False,
        log_level="debug" if config.MODE == "DEV" else "info",
    )
