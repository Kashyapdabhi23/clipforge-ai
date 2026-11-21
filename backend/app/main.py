import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database.session import init_db
from app.core.config import STORAGE_DIR, UPLOADS_DIR, CLIPS_DIR, THUMBNAILS_DIR
from app.api import routes_upload, routes_jobs, routes_projects, routes_clips, routes_health
from app.core.logging import logger

# Initialize database
init_db()

app = FastAPI(
    title="ClipForge AI API",
    description="Automated AI Video Clipping & Highlight Generation Engine",
    version="1.0.0"
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static file serving for videos, clips, and thumbnails
app.mount("/static/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")
app.mount("/static/clips", StaticFiles(directory=str(CLIPS_DIR)), name="clips")
app.mount("/static/thumbnails", StaticFiles(directory=str(THUMBNAILS_DIR)), name="thumbnails")

# Register API routers
app.include_router(routes_health.router)
app.include_router(routes_upload.router)
app.include_router(routes_jobs.router)
app.include_router(routes_projects.router)
app.include_router(routes_clips.router)

@app.on_event("startup")
async def startup_event():
    import asyncio
    from app.models.models import ProcessingJob
    from app.database.session import SessionLocal
    from app.services.job_queue import execute_processing_pipeline

    logger.info("ClipForge AI Backend initialized and ready on CPU.")
    db = SessionLocal()
    queued_jobs = db.query(ProcessingJob).filter(ProcessingJob.status == "QUEUED").all()
    for qj in queued_jobs:
        logger.info(f"Dispatching pending queued job: {qj.id}")
        asyncio.create_task(execute_processing_pipeline(qj.id))
    db.close()

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)
