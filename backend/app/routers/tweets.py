from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import Tweet
from app.schemas import TweetOut
import uuid
from typing import Optional

router = APIRouter(prefix="/api/tweets", tags=["tweets"])


@router.get("", response_model=list[TweetOut])
async def list_tweets(
    status: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
):
    query = select(Tweet).order_by(Tweet.fetched_at.desc()).limit(limit).offset(offset)
    if status:
        query = query.where(Tweet.status == status)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{tweet_id}", response_model=TweetOut)
async def get_tweet(tweet_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Tweet).where(Tweet.id == tweet_id))
    tweet = result.scalar_one_or_none()
    if not tweet:
        raise HTTPException(status_code=404, detail="Tweet not found")
    return tweet
