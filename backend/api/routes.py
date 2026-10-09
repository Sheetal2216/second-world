from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def root():
    return {"message": "SECOND WORLD backend is running!"}