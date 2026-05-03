from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import settings as settings_router, tweets, scripts, jobs

app = FastAPI(
    title="AI Content Pipeline",
    description="Automated TikTok script generator from Twitter bookmarks",
    version="1.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(settings_router.router)
app.include_router(tweets.router)
app.include_router(scripts.router)
app.include_router(jobs.router)


@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.1.0"}
