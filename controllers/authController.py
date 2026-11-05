from fastapi import HTTPException
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
import os
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from server.models.User import User
from server.models.Payment import Payment
from pydantic import BaseModel
from typing import Optional

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- Schemas ---
class RegisterSchema(BaseModel):
    phone: str
    password: str
    storeNumber: str
    deviceId: Optional[str] = None

class LoginSchema(BaseModel):
    phone: str
    password: str

class ResetPasswordSchema(BaseModel):
    phone: str
    newPassword: str

class AdminLoginSchema(BaseModel):
    username: str
    password: str

# --- Helpers ---
async def find_user_flex(db: AsyncSession, phone: str):
    normalized = phone.strip()
    user = await db.scalar(select(User).where(User.phone == normalized))
    if not user:
        alt = normalized[3:] if normalized.startswith("252") else "252" + normalized
        user = await db.scalar(select(User).where(User.phone == alt))
    return user

async def find_payment_flex(db: AsyncSession, phone: str):
    normalized = phone.strip()
    payment = await db.get(Payment, normalized)
    if not payment:
        alt = normalized[3:] if normalized.startswith("252") else "252" + normalized
        payment = await db.get(Payment, alt)
    return payment

# --- Controllers ---
async def register(data: RegisterSchema, db: AsyncSession):
    clean_phone = data.phone.strip()
    existing_user = await find_user_flex(db, clean_phone)
    existing_by_store = await db.scalar(select(User).where(User.storeNumber == data.storeNumber.strip()))
    
    if existing_by_store and (not existing_user or existing_by_store.phone != existing_user.phone):
        raise HTTPException(status_code=400, detail="Store already taken.")

    hashed_password = pwd_context.hash(data.password)

    if existing_user:
        existing_user.password = hashed_password
        existing_user.storeNumber = data.storeNumber.strip()
        existing_user.deviceId = data.deviceId.strip() if data.deviceId else "Unknown"

        payment = await find_payment_flex(db, existing_user.phone)
        await db.commit()
        if payment and payment.expiryDate and payment.expiryDate > datetime.utcnow():
            return {"message": "Account updated. Remaining days preserved."}
        return {"message": "Account updated. No active subscription found."}
    else:
        new_user = User(
            phone=clean_phone,
            password=hashed_password,
            storeNumber=data.storeNumber.strip(),
            deviceId=data.deviceId.strip() if data.deviceId else "Unknown"
        )
        db.add(new_user)

        payment = await find_payment_flex(db, clean_phone)
        if payment:
            if payment.expiryDate and payment.expiryDate > datetime.utcnow():
                await db.commit()
                return {"message": "Welcome back! Your remaining days have been restored."}
            else:
                await db.commit()
                return {"message": "Registration successful. Your subscription is expired, please renew."}
        else:
            payment = Payment(
                phone=clean_phone,
                isPaid=True,
                expiryDate=datetime.utcnow() + timedelta(days=30)
            )
            db.add(payment)
            await db.commit()
            return {"message": "Registration successful. 30-day trial activated."}

async def login(data: LoginSchema, db: AsyncSession):
    user = await find_user_flex(db, data.phone)
    if not user or not pwd_context.verify(data.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"message": "Login successful", "storeNumber": user.storeNumber}

async def reset_password(data: ResetPasswordSchema, db: AsyncSession):
    user = await find_user_flex(db, data.phone)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.password = pwd_context.hash(data.newPassword)
    await db.commit()
    return {"message": "Password updated successfully"}

async def unlink_device(phone: str, db: AsyncSession):
    user = await find_user_flex(db, phone)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.deviceId = None
    await db.commit()
    return {"message": f"Device unlinked for {phone}."}

async def admin_login(data: AdminLoginSchema):
    admin_user = os.getenv("ADMIN_USERNAME")
    admin_pass = os.getenv("ADMIN_PASSWORD")
    admin_secret = os.getenv("ADMIN_SECRET_KEY")

    if not admin_user or not admin_pass or not admin_secret:
        raise HTTPException(status_code=500, detail="Server security configuration incomplete")

    if data.username == admin_user and data.password == admin_pass:
        token = jwt.encode(
            {"role": "admin", "user": data.username, "exp": datetime.utcnow() + timedelta(hours=12)},
            admin_secret, algorithm="HS256"
        )
        return {"message": "Admin login successful", "token": token}
    else:
        raise HTTPException(status_code=401, detail="Invalid admin credentials")

async def get_all_users(db: AsyncSession):
    users = (await db.scalars(select(User))).all()
    phones = [user.phone for user in users]
    payments = (await db.scalars(select(Payment).where(Payment.phone.in_(phones)))).all() if phones else []
    payments_by_phone = {payment.phone: payment for payment in payments}
    user_list = []
    for user in users:
        payment = payments_by_phone.get(user.phone)
        now = datetime.utcnow()
        days_remaining = max(0, (payment.expiryDate - now).days) if payment and payment.expiryDate else 0
        user_list.append({
            "phone": user.phone,
            "storeNumber": user.storeNumber,
            "deviceId": user.deviceId,
            "daysRemaining": days_remaining,
            "isSuspended": payment.isSuspended if payment else False
        })
    return user_list

async def delete_user(phone: str, db: AsyncSession):
    user = await find_user_flex(db, phone)
    if user:
        await db.delete(user)
        await db.commit()
    return {"message": "User credentials cleared successfully. Subscription days preserved."}
