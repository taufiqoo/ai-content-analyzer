from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import NicheConfig
from app.schemas import NicheConfigCreate, NicheConfigUpdate, NicheConfigOut
import uuid

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("/niche", response_model=list[NicheConfigOut])
async def list_niches(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(NicheConfig).order_by(NicheConfig.created_at))
    return result.scalars().all()


@router.post("/niche", response_model=NicheConfigOut)
async def create_niche(body: NicheConfigCreate, db: AsyncSession = Depends(get_db)):
    niche = NicheConfig(**body.model_dump())
    db.add(niche)
    await db.commit()
    await db.refresh(niche)
    return niche


@router.put("/niche/{niche_id}", response_model=NicheConfigOut)
async def update_niche(
    niche_id: uuid.UUID,
    body: NicheConfigUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(NicheConfig).where(NicheConfig.id == niche_id))
    niche = result.scalar_one_or_none()
    if not niche:
        raise HTTPException(status_code=404, detail="Niche config not found")

    for field, value in body.model_dump(exclude_none=True).items():
        setattr(niche, field, value)

    await db.commit()
    await db.refresh(niche)
    return niche


@router.delete("/niche/{niche_id}")
async def delete_niche(niche_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(NicheConfig).where(NicheConfig.id == niche_id))
    niche = result.scalar_one_or_none()
    if not niche:
        raise HTTPException(status_code=404, detail="Niche config not found")
    await db.delete(niche)
    await db.commit()
    return {"ok": True}
