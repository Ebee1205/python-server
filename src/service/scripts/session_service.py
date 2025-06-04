from datetime import datetime
from uuid import uuid4

# Session ID 생성 함수
def generate_sid() -> str:
    return f"s-{uuid4().hex[:10]}"

# Message ID 생성 함수
def generate_mid() -> str:
    return f"m-{uuid4().hex[:10]}"