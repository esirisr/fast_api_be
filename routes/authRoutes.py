from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from server.config.db import get_db
from server.controllers import authController
from server.middleware.auth import admin_auth

router = APIRouter()

@router.post("/register")
async def register(data: authController.RegisterSchema, db: AsyncSession = Depends(get_db)):
    return await authController.register(data, db)

@router.post("/login")
async def login(data: authController.LoginSchema, db: AsyncSession = Depends(get_db)):
    return await authController.login(data, db)

@router.post("/reset-password")
async def reset_password(data: authController.ResetPasswordSchema, db: AsyncSession = Depends(get_db)):
    return await authController.reset_password(data, db)

@router.post("/admin/unlink-device")
async def unlink_device(phone: str, admin = Depends(admin_auth), db: AsyncSession = Depends(get_db)):
    return await authController.unlink_device(phone, db)

@router.post("/admin/login")
async def admin_login(data: authController.AdminLoginSchema):
    return await authController.admin_login(data)

@router.get("/users")
async def get_all_users(admin = Depends(admin_auth), db: AsyncSession = Depends(get_db)):
    return await authController.get_all_users(db)

@router.delete("/users/{phone}")
async def delete_user(phone: str, admin = Depends(admin_auth), db: AsyncSession = Depends(get_db)):
    return await authController.delete_user(phone, db)
