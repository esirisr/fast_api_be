from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from contextlib import asynccontextmanager
import os
from pathlib import Path
from dotenv import load_dotenv

from server.config.db import close_db, init_db
from server.routes import authRoutes, statusRoutes
from server.middleware.logger import logger_middleware

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    print("PostgreSQL Connected Successfully")
    try:
        yield
    finally:
        await close_db()

app = FastAPI(title="AutoSender API", lifespan=lifespan)

# CORS Middleware
frontend_origins = [
    origin.strip().rstrip("/")
    for origin in os.getenv(
        "FRONTEND_ORIGINS",
        "https://himiloffe.up.railway.app",
    ).split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=frontend_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logger Middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    return await logger_middleware(request, call_next)

@app.get("/")
def read_root():
    return FileResponse(Path(__file__).resolve().parent.parent / "index.html")

# Include Routes
app.include_router(authRoutes.router)
app.include_router(statusRoutes.router, prefix="/status")

# Global Error Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"ERROR: {exc}")
    return JSONResponse(status_code=500, content={"message": "Internal Server Error"})

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 3000))
    uvicorn.run("server.main:app", host="0.0.0.0", port=port, reload=True)
