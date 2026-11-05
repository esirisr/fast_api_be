from fastapi import APIRouter

router = APIRouter()

@router.get("/check")
def get_status():
    return {"status": "active", "health": "good"}
