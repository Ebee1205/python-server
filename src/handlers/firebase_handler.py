import threading
import firebase_admin
from firebase_admin import credentials, firestore

class FirebaseHandler:
    """
    Firebase Firestore 핸들러 클래스입니다.
    서버리스 환경에서 Firestore 연동을 간편하게 처리합니다.
    """
    def __init__(self, ctx):
        self.ctx = ctx
        self.log = ctx.log
        self.db = None
        self.app = None
        self.lock = threading.Lock()

    def connect(self):
        """
        ctx.cfg.firebase 설정을 사용하여 Firebase 앱과 Firestore 클라이언트를 초기화합니다.
        ctx.cfg.firebase 에는 'project_id' 와 'credentials_path'가 있어야 합니다.
        """
        with self.lock:
            if self.db is not None:
                return
            try:
                conf = self.ctx.cfg.firebase
                cred = credentials.Certificate(conf.credentials_path)
                self.app = firebase_admin.initialize_app(
                    cred,
                    {'projectId': conf.project_id}
                )
                self.db = firestore.client()
                self.log.info(f"[Firebase] ++ Firestore 연결됨 (project={conf.project_id})")
            except Exception as e:
                self.log.error(f"[Firebase] -- 연결 실패: {e}")
                self.db = None

    def get_client(self) -> firestore.Client:
        """
        Firestore 클라이언트 반환 전 연결을 보장합니다.
        """
        if self.db is None:
            self.log.warning("[Firebase] -- 연결되지 않음, connect() 호출")
            self.connect()
        return self.db

    def disconnect(self):
        """
        Firebase Admin SDK는 Firestore 별도 해제 불필요.
        내부 참조(app, db)를 정리합니다.
        """
        with self.lock:
            if self.app:
                try:
                    firebase_admin.delete_app(self.app)
                    self.log.info("[Firebase] -- 앱 삭제됨")
                except Exception as e:
                    self.log.warning(f"[Firebase] -- 앱 삭제 실패: {e}")
                finally:
                    self.app = None
                    self.db = None