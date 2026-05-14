from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm

from src.core.responses import build_response_body, build_success_response, ResponseStatus
from src.service.auth import auth_service
from src.service.auth.auth_schema import UserCreate, UserLogin, UserExistsRequest, CheckEmailRequest, UserUpdateRequest
from src.service.auth.jwt_auth import require_user

router = APIRouter(prefix="/api/auth", tags=["Auth"])

@router.post("/signup", status_code=201)
async def signup(request: Request, user: UserCreate):
    """
    회원가입 API
    """
    ctx = request.app.state.ctx
    
    # 비밀번호 확인 체크
    if user.password and user.passwordCheck:
        if user.password != user.passwordCheck:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password match failed"
            )

    newUser = auth_service.create_user(ctx, user)
    return build_response_body(ResponseStatus.CREATED, newUser)

@router.post("/login")
async def login(request: Request, loginReq: UserLogin):
    """
    로그인 API (JSON Body)
    """
    ctx = request.app.state.ctx
    user = auth_service.authenticate_user(ctx, loginReq.email, loginReq.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    accessToken = auth_service.create_access_token(
        ctx, 
        data={"sub": user["email"], "role": user["role"]}
    )
    return build_success_response({"accessToken": accessToken, "tokenType": "bearer"})


@router.post("/token")
async def loginForm(request: Request, formData: OAuth2PasswordRequestForm = Depends()):
    """
    Swagger UI용 로그인 API (Form Data)
    """
    ctx = request.app.state.ctx
    user = auth_service.authenticate_user(ctx, formData.username, formData.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    accessToken = auth_service.create_access_token(
        ctx, 
        data={"sub": user["email"], "role": user["role"]}
    )
    return build_success_response({"accessToken": accessToken, "tokenType": "bearer"})

@router.get("/me")
async def readUsersMe(request: Request, user=Depends(require_user)):
    """
    현재 사용자 정보 조회 (JWT 인증)
    """
    return build_success_response(user)


@router.post("/exists")
async def checkExists(request: Request, body: UserExistsRequest):
    """
    사용자 ID 존재 여부 체크
    """
    ctx = request.app.state.ctx
    exists = auth_service.check_user_exists(ctx, body.id)
    return build_success_response({"id": body.id, "exists": exists})


@router.post("/checkEmail")
async def checkEmail(request: Request, body: CheckEmailRequest):
    """
    이메일 유효성 및 중복 체크
    """
    ctx = request.app.state.ctx
    exists = auth_service.check_email_exists(ctx, body.email)
    return build_success_response({"email": body.email, "exists": exists})


@router.post("/logout")
async def logout(user=Depends(require_user)):
    """
    로그아웃 (JWT는 stateless이므로 클라이언트에서 토큰 삭제)
    """
    return build_success_response({"message": "Logged out successfully"})


@router.post("/update")
async def updateUser(request: Request, body: UserUpdateRequest, user=Depends(require_user)):
    """
    내 정보 수정 (JWT 인증)
    """
    ctx = request.app.state.ctx
    result = auth_service.update_user(ctx, user["id"], body.model_dump(exclude_none=True))
    return build_success_response(result)
