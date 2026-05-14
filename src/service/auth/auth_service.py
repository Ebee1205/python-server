from datetime import datetime, timedelta
from typing import Optional
import jwt  # Using PyJWT or python-jose
from fastapi import HTTPException
from passlib.context import CryptContext

from src.app_context import AppContext
from src.utils.db_utils import execute_query
from src.service.auth.auth_schema import UserCreate, UserRole, UserState

# 비밀번호 해싱 설정
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

ALGORITHM = "HS256"


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plainPassword: str, hashedPassword: str) -> bool:
    if not hashedPassword:
        return False
    return pwd_context.verify(plainPassword, hashedPassword)

def create_access_token(ctx: AppContext, data: dict, expiresDelta: Optional[timedelta] = None) -> str:
    toEncode = data.copy()
    if expiresDelta:
        expire = datetime.utcnow() + expiresDelta
    else:
        # Default expiration from config
        expireMinutes = getattr(ctx.cfg, "access_token_expire_minutes", 60)
        expire = datetime.utcnow() + timedelta(minutes=expireMinutes)
    
    toEncode.update({"exp": expire})
    secretKey = ctx.cfg.secret_key
    encodedJwt = jwt.encode(toEncode, secretKey, algorithm=ALGORITHM)
    return encodedJwt


def get_user_by_email(ctx: AppContext, email: str, activeOnly: bool = True) -> Optional[dict]:
    sql = """
        SELECT id, email, password, name, nickname, phone,
               emailConf, `desc`, fileId, role, state, extra
        FROM tb_user
        WHERE email = %s
    """
    params = [email]
    if activeOnly:
        sql += " AND state = %s"
        params.append(UserState.ACTIVE.value)

    if not ctx.db_handler:
        return None

    rows = execute_query(ctx.db_handler, sql, tuple(params))
    if not rows:
        return None

    row = rows[0]
    extra = row[11] or {}
    if isinstance(extra, str):
        import json as _json
        extra = _json.loads(extra)

    return {
        "id": row[0],
        "email": row[1],
        "password": row[2],
        "name": row[3],
        "nickname": row[4],
        "phone": row[5],
        "emailConf": row[6],
        "desc": row[7],
        "fileId": row[8],
        "role": row[9],
        "state": row[10],
        "extra": extra,
        "provider": extra.get("provider", "email"),
        "providerId": extra.get("providerId"),
    }


def create_user(ctx: AppContext, user: UserCreate) -> dict:
    if ctx.db_handler is None:
         # DB 연결이 없을 경우 에러 처리 혹은 Mocking
        raise HTTPException(status_code=500, detail="Database not initialized")

    existing = get_user_by_email(ctx, user.email, activeOnly=False)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashedPassword = get_password_hash(user.password) if user.password else None

    role = UserRole.CLIENT

    # provider/providerId는 extra JSON에 저장
    import json as _json
    import time as _time
    extra = dict(user.extra) if user.extra else {}
    if user.provider and user.provider != "email":
        extra["provider"] = user.provider
    if user.providerId:
        extra["providerId"] = user.providerId

    now = int(_time.time())

    sql = """
        INSERT INTO tb_user (
            name, nickname, email, password, phone,
            emailConf, `desc`, fileId, role, state, extra, cDate, uDate
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    params = (
        user.name, user.nickname, user.email, hashedPassword,
        user.phone, user.emailConf, user.desc, user.fileId,
        role.value, UserState.ACTIVE.value, _json.dumps(extra, ensure_ascii=False), now, now
    )

    conn = ctx.db_handler.get_connection()
    new_id: int | None = None
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            new_id = cursor.lastrowid
            conn.commit()
    except Exception as e:
        conn.rollback()
        ctx.log.error(f"Failed to create user: {e}")
        raise HTTPException(status_code=500, detail="Failed to create user")

    return {
        "id": new_id,
        "email": user.email,
        "name": user.name,
        "nickname": user.nickname,
        "role": role.value,
        "state": UserState.ACTIVE.value,
        "provider": user.provider,
    }


def authenticate_user(ctx: AppContext, email: str, password: str):
    user = get_user_by_email(ctx, email)
    if not user:
        return False
    if not verify_password(password, user["password"]):
        return False
    return user


def check_user_exists(ctx: AppContext, userId: int) -> bool:
    sql = "SELECT id FROM tb_user WHERE id = %s AND state = %s"
    if not ctx.db_handler:
        return False
    rows = execute_query(ctx.db_handler, sql, (userId, UserState.ACTIVE.value))
    return bool(rows)


def check_email_exists(ctx: AppContext, email: str) -> bool:
    sql = "SELECT id FROM tb_user WHERE email = %s AND state = %s"
    if not ctx.db_handler:
        return False
    rows = execute_query(ctx.db_handler, sql, (email, UserState.ACTIVE.value))
    return bool(rows)

def update_user(ctx: AppContext, userId: int, data: dict) -> dict:
    import json as _json
    import time as _time
    if ctx.db_handler is None:
        raise HTTPException(status_code=500, detail="Database not initialized")

    # 비밀번호 변경 처리
    if data.get("passwordNew"):
        if data.get("passwordNew") != data.get("passwordNewCheck"):
            raise HTTPException(status_code=400, detail="New password mismatch")
        sql = "SELECT id, email, password FROM tb_user WHERE id = %s"
        rows = execute_query(ctx.db_handler, sql, (userId,))
        if not rows:
            raise HTTPException(status_code=404, detail="User not found")
        if data.get("password") and not verify_password(data["password"], rows[0][2]):
            raise HTTPException(status_code=400, detail="Current password incorrect")
        data["password"] = get_password_hash(data["passwordNew"])

    fields = []
    params = []
    for key in ["name", "nickname", "phone", "desc", "fileId", "password"]:
        if data.get(key) is not None:
            colName = "`desc`" if key == "desc" else key
            fields.append(f"{colName} = %s")
            params.append(data[key])
    if data.get("extra") is not None:
        fields.append("extra = %s")
        params.append(_json.dumps(data["extra"], ensure_ascii=False))

    if not fields:
        raise HTTPException(status_code=400, detail="No fields to update")

    now = int(_time.time())
    fields.append("uDate = %s")
    params.append(now)
    params.append(userId)

    sql = f"UPDATE tb_user SET {', '.join(fields)} WHERE id = %s"
    conn = ctx.db_handler.get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            conn.commit()
    except Exception as e:
        conn.rollback()
        ctx.log.error(f"Failed to update user: {e}")
        raise HTTPException(status_code=500, detail="Failed to update user")

    return {"id": userId, "updated": True}
