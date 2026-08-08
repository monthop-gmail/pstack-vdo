from fastapi import APIRouter

router = APIRouter(prefix="/api/demo", tags=["demo"])


@router.get("/ping")
async def ping() -> dict:
    return {"module": "demo", "status": "ok"}
