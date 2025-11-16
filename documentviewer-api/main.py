from fastapi import FastAPI

from config import config
from routers.files.router import router as files_router

app = FastAPI(
    title="Document Viewer API",
    description="API for document viewer",
    version=config.VERSION,
    docs_url="/docs",
)

app.include_router(files_router)


@app.get("/health")
def health():
    return {
        "status": "OK",
        "mode": config.MODE,
        "version": config.VERSION,
        "docs_url": "/docs" if config.MODE == "DEV" else None,
    }
