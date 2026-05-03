from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import uuid


# ── Niche Config ──────────────────────────────────────────────────────────────

class NicheConfigBase(BaseModel):
    name: str
    keywords: List[str] = []
    hook_formulas: List[str] = []
    script_rules: Optional[str] = None
    example_scripts: List[dict] = []
    target_duration_seconds: int = 60
    is_active: bool = True


class NicheConfigCreate(NicheConfigBase):
    pass


class NicheConfigUpdate(BaseModel):
    name: Optional[str] = None
    keywords: Optional[List[str]] = None
    hook_formulas: Optional[List[str]] = None
    script_rules: Optional[str] = None
    example_scripts: Optional[List[dict]] = None
    target_duration_seconds: Optional[int] = None
    is_active: Optional[bool] = None


class NicheConfigOut(NicheConfigBase):
    id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Tweet ──────────────────────────────────────────────────────────────────────

class TweetOut(BaseModel):
    id: uuid.UUID
    tweet_id: str
    author_username: Optional[str]
    content: Optional[str]
    url: Optional[str]
    has_article_link: bool
    article_url: Optional[str]
    article_content: Optional[str]
    relevance_score: Optional[float]
    relevance_reason: Optional[str]
    niche_config_id: Optional[uuid.UUID]
    status: str
    fetched_at: datetime

    model_config = {"from_attributes": True}


# ── Script ────────────────────────────────────────────────────────────────────

class ScriptOut(BaseModel):
    id: uuid.UUID
    tweet_id: uuid.UUID
    angle: Optional[str]
    hook: str
    body: str
    cta: str
    full_script: str
    hook_formula_used: Optional[str]
    duration_estimate: Optional[int]
    naturalness_score: Optional[float]
    status: str
    claude_model: Optional[str]
    user_feedback: Optional[str]
    created_at: datetime
    approved_at: Optional[datetime]
    tweet: Optional[TweetOut] = None
    performance: Optional["ScriptPerformanceOut"] = None

    model_config = {"from_attributes": True}


class ScriptUpdate(BaseModel):
    hook: Optional[str] = None
    body: Optional[str] = None
    cta: Optional[str] = None
    full_script: Optional[str] = None
    status: Optional[str] = None
    user_feedback: Optional[str] = None


# ── Script Performance ─────────────────────────────────────────────────────────

class ScriptPerformanceCreate(BaseModel):
    views: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    watch_time_percent: Optional[float] = None
    did_fyp: bool = False
    notes: Optional[str] = None


class ScriptPerformanceOut(BaseModel):
    id: uuid.UUID
    script_id: uuid.UUID
    views: int
    likes: int
    comments: int
    shares: int
    watch_time_percent: Optional[float]
    did_fyp: bool
    notes: Optional[str]
    recorded_at: datetime

    model_config = {"from_attributes": True}


ScriptOut.model_rebuild()


# ── Pipeline ───────────────────────────────────────────────────────────────────

class PipelineJobOut(BaseModel):
    id: uuid.UUID
    celery_task_id: Optional[str]
    status: str
    step: Optional[str]
    tweets_fetched: int
    tweets_relevant: int
    scripts_generated: int
    error_message: Optional[str]
    started_at: datetime
    completed_at: Optional[datetime]

    model_config = {"from_attributes": True}


class ManualArticleIn(BaseModel):
    content: str = Field(..., min_length=100, description="Full article text to generate scripts from")
    niche_config_id: Optional[str] = None
    title: Optional[str] = None
