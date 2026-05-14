from __future__ import annotations

from fastapi import APIRouter, Request, UploadFile, File, Form, HTTPException, Depends
import orjson

from src.core.responses import build_success_response
from src.service.auth.jwt_auth import require_user
from src.service.files import files_service
from src.service.files.files_schema import FileIdRequest, FileListResponse

router = APIRouter(prefix="/api/files", tags=["Files"])

@router.post("/create", status_code=201)
async def create_file(
    request: Request,
    file: UploadFile = File(...),
    uploadType: str = Form(..., alias="type", description="Upload type (profile, reference, snap, temp)"),
    metadata: str | None = Form(None),
    user=Depends(require_user),
):
    ctx = request.app.state.ctx

    meta_dict = None
    if metadata:
        try:
            meta_dict = orjson.loads(metadata)
        except Exception:
            raise HTTPException(status_code=400, detail="metadata must be JSON string")

    stored = await files_service.save_file(
        ctx,
        file,
        meta_dict,
        upload_type=uploadType,
        user_id=user.get("id"),
    )
    return build_success_response(stored)


@router.post("/list")
async def list_all_files(_=Depends(require_user)):
    files = files_service.list_files()
    return build_success_response(FileListResponse(files=files, total=len(files)))


@router.post("/get")
async def get_file_meta(payload: FileIdRequest, _=Depends(require_user)):
    info = files_service.get_file(payload.fileId)
    if not info:
        raise HTTPException(status_code=404, detail="file not found")
    return build_success_response(info)


@router.post("/delete")
async def delete_file(request: Request, payload: FileIdRequest, _=Depends(require_user)):
    ctx = request.app.state.ctx
    info = await files_service.delete_file(ctx, payload.fileId)
    if not info:
        raise HTTPException(status_code=404, detail="file not found")
    return build_success_response({"fileId": payload.fileId})


@router.post("/getPresigned")
async def get_presigned_url(request: Request, payload: FileIdRequest, _=Depends(require_user)):
    ctx = request.app.state.ctx
    url = await files_service.get_presigned_url(ctx, payload.fileId)
    if not url:
        raise HTTPException(status_code=404, detail="file not found")
    return build_success_response({"url": url})
