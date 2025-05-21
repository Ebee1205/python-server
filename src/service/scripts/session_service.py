from datetime import datetime
from uuid import uuid4

# SID 생성 함수
def generate_sid() -> str:
    return f"s-{uuid4().hex[:10]}"