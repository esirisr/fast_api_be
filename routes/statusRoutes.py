from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from server.config.db import get_db
from server.controllers import statusController
from server.middleware.auth import admin_auth

router = APIRouter()

@router.get("/check")
async def health_check():
    return {"status": "active", "health": "good"}

@router.get("/analytics")
async def get_analytics(admin = Depends(admin_auth), db: AsyncSession = Depends(get_db)):
    return await statusController.get_analytics(db)

@router.get("/check-store")
async def check_store_unique(
    phone: str = Query(...), 
    store: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    return await statusController.check_store_unique(phone, store, db)

@router.get("/{phone}")
async def get_status(phone: str, db: AsyncSession = Depends(get_db)):
    return await statusController.get_status(phone, db)

@router.put("/{phone}")
async def update_payment_status(
    phone: str, 
    data: statusController.UpdatePaymentSchema, 
    admin = Depends(admin_auth),
    db: AsyncSession = Depends(get_db),
):
    return await statusController.update_payment_status(phone, data, db)
