from fastapi import APIRouter, Request
from src.service.scripts import basic_service

router = APIRouter(prefix="/api/basic", tags=["Basic"])

@router.get("/ping")
async def ping(request: Request):
    ctx = request.app.state.ctx
    return basic_service.ping(ctx)
