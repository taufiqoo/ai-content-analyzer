import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Text, Float, Boolean, Integer,
    DateTime, ForeignKey, ARRAY, JSON
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class NicheConfig(Base):
    __tablename__ = "niche_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    keywords = Column(ARRAY(Text), default=[])
    hook_formulas = Column(ARRAY(Text), default=[])
    script_rules = Column(Text, nullable=True)
    example_scripts = Column(JSON, default=[])
    target_duration_seconds = Column(Integer, default=60)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    tweets = relationship("Tweet", back_populates="niche_config")


class Tweet(Base):
    __tablename__ = "tweets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tweet_id = Column(String(50), unique=True, nullable=False)
    author_username = Column(String(100), nullable=True)
    content = Column(Text, nullable=True)
    url = Column(Text, nullable=True)
    has_article_link = Column(Boolean, default=False)
    article_url = Column(Text, nullable=True)
    article_content = Column(Text, nullable=True)
    relevance_score = Column(Float, nullable=True)
    relevance_reason = Column(Text, nullable=True)
    niche_config_id = Column(UUID(as_uuid=True), ForeignKey("niche_configs.id"), nullable=True)
    # pending | relevant | irrelevant | scripted
    status = Column(String(20), default="pending")
    fetched_at = Column(DateTime, default=datetime.utcnow)

    niche_config = relationship("NicheConfig", back_populates="tweets")
    scripts = relationship("Script", back_populates="tweet")


class Script(Base):
    __tablename__ = "scripts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tweet_id = Column(UUID(as_uuid=True), ForeignKey("tweets.id"), nullable=False)
    angle = Column(String(100), nullable=True)
    hook = Column(Text, nullable=False)
    body = Column(Text, nullable=False)
    cta = Column(Text, nullable=False)
    full_script = Column(Text, nullable=False)
    hook_formula_used = Column(String(200), nullable=True)
    duration_estimate = Column(Integer, nullable=True)
    naturalness_score = Column(Float, nullable=True)
    # draft | approved | rejected
    status = Column(String(20), default="draft")
    claude_model = Column(String(50), nullable=True)
    prompt_used = Column(Text, nullable=True)
    user_feedback = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    approved_at = Column(DateTime, nullable=True)

    tweet = relationship("Tweet", back_populates="scripts")
    performance = relationship("ScriptPerformance", back_populates="script", uselist=False)


class ScriptPerformance(Base):
    __tablename__ = "script_performance"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    script_id = Column(UUID(as_uuid=True), ForeignKey("scripts.id"), nullable=False)
    views = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    watch_time_percent = Column(Float, nullable=True)
    did_fyp = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)
    recorded_at = Column(DateTime, default=datetime.utcnow)

    script = relationship("Script", back_populates="performance")


class PipelineJob(Base):
    __tablename__ = "pipeline_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    celery_task_id = Column(String(200), nullable=True)
    # running | completed | failed
    status = Column(String(20), default="running")
    step = Column(String(100), nullable=True)
    tweets_fetched = Column(Integer, default=0)
    tweets_relevant = Column(Integer, default=0)
    scripts_generated = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
