from fastapi import APIRouter

router = APIRouter()

@router.get("/test-route")
def get_test_data():
    return {"message": "This is the 'kk' route returning data"}
