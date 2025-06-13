from fastapi.testclient import TestClient
from src.app_context import AppContext

class FakeLogger:
    def debug(self, message):
        pass  # 로깅 출력 제거

    def info(self, message):
        pass  # 로깅 출력 제거

    def warning(self, message):
        pass  # 로깅 출력 제거

class FakeDBHandler:
    def close(self):
        pass  # 실제 DB 연결 종료 안 함

    def execute(self, query, params=None):
        return []  # 실제 DB 쿼리 실행 안 함

    def fetchall(self):
        return []  # 실제 DB 결과 반환 안 함

class TestAppContext(AppContext):
    def __init__(self):
        super().__init__()
        self.log = FakeLogger()  # 로깅 출력 제거
        self.db_handler = FakeDBHandler()  # 실제 DB 사용 안 함

# 테스트 시작 전에 ctx 교체
