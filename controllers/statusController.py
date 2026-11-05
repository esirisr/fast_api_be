from fastapi import HTTPException
from datetime import datetime, timedelta
from server.models.Payment import Payment
from server.models.User import User
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

class UpdatePaymentSchema(BaseModel):
    isPaid: Optional[bool] = None
    isSuspended: Optional[bool] = None
    daysToAdd: Optional[int] = None
    daysToSet: Optional[int] = None

async def find_payment_flex(db: AsyncSession, phone: str):
    normalized = phone.strip()
    payment = await db.get(Payment, normalized)
    if not payment:
        alt = normalized[3:] if normalized.startswith("252") else "252" + normalized
        payment = await db.get(Payment, alt)
    return payment

async def get_status(phone: str, db: AsyncSession):
    payment = await find_payment_flex(db, phone)
    if not payment:
        raise HTTPException(status_code=404, detail="User not found")
    
    now = datetime.utcnow()
    is_active = bool(payment.isPaid and not payment.isSuspended and payment.expiryDate and payment.expiryDate > now)
    
    return {
        "phone": payment.phone,
        "isPaid": payment.isPaid,
        "isSuspended": payment.isSuspended,
        "expiryDate": payment.expiryDate,
        "isActive": is_active,
        "daysRemaining": max(0, (payment.expiryDate - now).days) if payment.expiryDate else 0,
        "message": "Your account has been suspended" if payment.isSuspended else None
    }

async def update_payment_status(phone: str, data: UpdatePaymentSchema, db: AsyncSession):
    payment = await find_payment_flex(db, phone)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment record not found")
    
    if data.isPaid is not None:
        payment.isPaid = data.isPaid
    if data.isSuspended is not None:
        payment.isSuspended = data.isSuspended
    
    now = datetime.utcnow()
    
    if data.daysToAdd:
        base_date = payment.expiryDate if payment.expiryDate and payment.expiryDate > now else now
        payment.expiryDate = base_date + timedelta(days=data.daysToAdd)
        
    if data.daysToSet is not None:
        payment.expiryDate = now + timedelta(days=data.daysToSet)
    
    payment.lastUpdated = now
    await db.commit()
    
    return {
        "message": "Status updated successfully",
        "phone": payment.phone,
        "newExpiry": payment.expiryDate,
        "daysRemaining": (payment.expiryDate - now).days if payment.expiryDate else 0
    }

async def check_store_unique(phone: str, store: str, db: AsyncSession):
    if not phone or not store:
        raise HTTPException(status_code=400, detail="Missing parameters")
    
    existing_owner = await db.scalar(select(User).where(User.storeNumber == store))
    
    if not existing_owner:
        user = await db.get(User, phone)
        if user:
            user.storeNumber = store
            await db.commit()
        return {"isActive": True, "message": "Store assigned"}
    
    if existing_owner.phone == phone:
        return {"isActive": True, "message": "Owner verified"}
    
    raise HTTPException(status_code=403, detail="PLEASE CREATE YOUR OWN ACCOUNT")

async def get_analytics(db: AsyncSession):
    now = datetime.utcnow()
    total_users = await db.scalar(select(func.count()).select_from(User)) or 0
    active_users = await db.scalar(
        select(func.count()).select_from(Payment).where(
            Payment.isPaid.is_(True),
            Payment.isSuspended.is_(False),
            Payment.expiryDate > now,
        )
    ) or 0
    suspended_users = await db.scalar(
        select(func.count()).select_from(Payment).where(Payment.isSuspended.is_(True))
    ) or 0
    
    latest_users = (await db.scalars(select(User).order_by(User.createdAt.desc()).limit(5))).all()
    
    return {
        "totalUsers": total_users,
        "activeUsers": active_users,
        "suspendedUsers": suspended_users,
        "inactiveUsers": total_users - active_users - suspended_users,
        "latestUsers": [{"phone": u.phone, "storeNumber": u.storeNumber} for u in latest_users]
    }
