from fastapi import Request, HTTPException, Depends
from fastapi.security import APIKeyHeader
from jose import jwt, JWTError
import os

api_key_header = APIKeyHeader(name="x-admin-key", auto_error=False)

async def admin_auth(request: Request, x_admin_key: str = Depends(api_key_header)):
    auth_header = request.headers.get("Authorization")
    admin_key = x_admin_key
    
    # Support both custom header and standard Authorization: Bearer <token>
    if not admin_key and auth_header and auth_header.startswith("Bearer "):
        admin_key = auth_header.split(" ")[1]

    secret_key = os.getenv("ADMIN_SECRET_KEY")

    if not secret_key:
        print("SECURITY ERROR: ADMIN_SECRET_KEY is missing.")
        raise HTTPException(status_code=500, detail="Server security configuration missing.")

    if not admin_key:
        raise HTTPException(status_code=403, detail="Access denied. No token provided.")

    try:
        verified = jwt.decode(admin_key, secret_key, algorithms=["HS256"])
        return verified
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired admin session.")
