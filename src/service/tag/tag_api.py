from fastapi import APIRouter, Depends, Request

from src.core.responses import build_success_response

from src.service.auth.jwt_auth import require_user
from src.service.tag import tag_service
from src.service.tag.tag_schema import (
	TagCreateRequest,
	TagDeleteRequest,
	TagGetRequest,
	TagListRequest,
	TagUpdateRequest,
)

router = APIRouter(prefix="/api/tag", tags=["Tag"])


@router.post("/list")
async def list_tags(request: Request, payload: TagListRequest, _=Depends(require_user)):
	"""태그 목록 조회"""
	ctx = request.app.state.ctx
	result = tag_service.list_tags(
		ctx,
		page=payload.page,
		limit=payload.limit,
		parent_code=payload.parentCode,
	)
	return build_success_response(result)


@router.post("/get")
async def get_tag(request: Request, payload: TagGetRequest, _=Depends(require_user)):
	"""태그 상세 조회"""
	ctx = request.app.state.ctx
	result = tag_service.get_tag(ctx, payload.id)
	return build_success_response(result)


@router.post("/create")
async def create_tag(request: Request, payload: TagCreateRequest, _=Depends(require_user)):
	"""태그 생성"""
	ctx = request.app.state.ctx
	result = tag_service.create_tag(ctx, payload)
	return build_success_response(result)


@router.post("/update")
async def update_tag(request: Request, payload: TagUpdateRequest, _=Depends(require_user)):
	"""태그 수정"""
	ctx = request.app.state.ctx
	result = tag_service.update_tag(ctx, payload)
	return build_success_response(result)


@router.post("/delete")
async def delete_tag(request: Request, payload: TagDeleteRequest, _=Depends(require_user)):
	"""태그 삭제"""
	ctx = request.app.state.ctx
	result = tag_service.delete_tag(ctx, payload.id)
	return build_success_response(result)
