from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models import PipelineJob, NicheConfig
from app.schemas import PipelineJobOut
from app.tasks import run_full_pipeline
from datetime import datetime
import uuid

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.post("/run-pipeline", response_model=PipelineJobOut)
async def trigger_pipeline(
    source: str = "bookmarks",
    limit: int = 30,
    db: AsyncSession = Depends(get_db),
):
    # Check niche config exists
    result = await db.execute(
        select(NicheConfig).where(NicheConfig.is_active == True).limit(1)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail="No active niche config found. Please create one in Settings first.",
        )

    job = PipelineJob(status="running", step="queued")
    db.add(job)
    await db.commit()
    await db.refresh(job)

    # Dispatch Celery task
    run_full_pipeline.delay(str(job.id), source=source, limit=limit)

    return job


@router.get("/status", response_model=list[PipelineJobOut])
async def list_jobs(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(PipelineJob).order_by(PipelineJob.started_at.desc()).limit(10)
    )
    return result.scalars().all()


@router.get("/status/{job_id}", response_model=PipelineJobOut)
async def get_job_status(job_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PipelineJob).where(PipelineJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/analytics/summary")
async def get_analytics_summary(db: AsyncSession = Depends(get_db)):
    from app.models import Tweet, Script, ScriptPerformance

    tweets_total = await db.execute(select(func.count(Tweet.id)))
    tweets_relevant = await db.execute(
        select(func.count(Tweet.id)).where(Tweet.status == "relevant")
    )
    tweets_scripted = await db.execute(
        select(func.count(Tweet.id)).where(Tweet.status == "scripted")
    )
    scripts_total = await db.execute(select(func.count(Script.id)))
    scripts_approved = await db.execute(
        select(func.count(Script.id)).where(Script.status == "approved")
    )
    fyp_count = await db.execute(
        select(func.count(ScriptPerformance.id)).where(
            ScriptPerformance.did_fyp == True
        )
    )
    total_views = await db.execute(select(func.sum(ScriptPerformance.views)))

    return {
        "tweets_total": tweets_total.scalar() or 0,
        "tweets_relevant": tweets_relevant.scalar() or 0,
        "tweets_scripted": tweets_scripted.scalar() or 0,
        "scripts_total": scripts_total.scalar() or 0,
        "scripts_approved": scripts_approved.scalar() or 0,
        "fyp_count": fyp_count.scalar() or 0,
        "total_views": total_views.scalar() or 0,
    }
