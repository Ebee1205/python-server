# handler/firebase_handler.py

import os
from google.cloud import firestore
from google.auth.exceptions import DefaultCredentialsError
from google.cloud.exceptions import GoogleCloudError
import firebase_admin
from firebase_admin import credentials, firestore as admin_firestore

class FirebaseHandler:
    """
    Firebase Firestore 핸들러 클래스입니다.
    서버리스 환경에서 Firestore 연동을 간편하게 처리합니다.
    """
    def __init__(self, ctx):
        self.ctx = ctx
        self.log = ctx.log
        self.cfg = ctx.cfg.firebase
        self.client: firestore.Client = None
        self._app = None

    def connect(self):
        """
        Firebase Firestore에 연결합니다.
        서비스 계정 키 파일 또는 환경 변수를 통해 인증합니다.
        """
        try:
            if self.client:
                self.log.info("[DB-firebase]     == Already connected")
                return

            self.log.debug("[DB-firebase]     - Connecting...")
            
            # Firebase Admin SDK 초기화
            if not firebase_admin._apps:
                if self.cfg.service_account_path:
                    # 서비스 계정 키 파일 사용
                    if os.path.exists(self.cfg.service_account_path):
                        cred = credentials.Certificate(self.cfg.service_account_path)
                        self._app = firebase_admin.initialize_app(cred, {
                            'projectId': self.cfg.project_id
                        })
                        self.log.debug("[DB-firebase]     - Using service account key file")
                    else:
                        self.log.error(f"[DB-firebase]     -- Service account file not found: {self.cfg.service_account_path}")
                        raise FileNotFoundError(f"Service account file not found: {self.cfg.service_account_path}")
                else:
                    # 기본 자격 증명 사용 (환경 변수 또는 Google Cloud 환경)
                    self._app = firebase_admin.initialize_app()
                    self.log.debug("[DB-firebase]     - Using default credentials")
            else:
                self._app = firebase_admin.get_app()

            # Firestore 클라이언트 생성
            if self.cfg.use_admin_sdk:
                # Firebase Admin SDK 사용
                self.client = admin_firestore.client(self._app)
            else:
                # Google Cloud Firestore 클라이언트 사용
                if self.cfg.service_account_path and os.path.exists(self.cfg.service_account_path):
                    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = self.cfg.service_account_path
                
                self.client = firestore.Client(project=self.cfg.project_id)

            # 연결 테스트
            test_collection = self.client.collection('_connection_test')
            test_doc = test_collection.document('test')
            test_doc.set({'timestamp': firestore.SERVER_TIMESTAMP})
            
            self.log.info("[DB-firebase]     == Connected successfully")

        except (DefaultCredentialsError, GoogleCloudError, Exception) as e:
            self.log.error(f"[DB-firebase]     -- Connection error: {str(e)}")
            raise

    def get_client(self) -> firestore.Client:
        """
        Firestore 클라이언트를 반환합니다.
        """
        if not self.client:
            self.log.error("[DB-firebase]     - Client not connected")
            raise RuntimeError("Firebase client is not connected")
        return self.client

    def disconnect(self):
        """
        Firebase 연결을 해제합니다.
        """
        try:
            if self.client:
                self.log.debug("[DB-firebase]     - Disconnecting...")
                
                # Firestore 클라이언트는 명시적인 close() 메서드가 없음
                # 대신 참조를 제거하여 가비지 컬렉션되도록 함
                self.client = None
                
                # Firebase Admin App 삭제
                if self._app:
                    firebase_admin.delete_app(self._app)
                    self._app = None
                
                self.log.info("[DB-firebase]     -- Disconnected")
        except Exception as e:
            self.log.warning(f"[DB-firebase]     - Disconnect failed: {str(e)}")

    def health_check(self) -> bool:
        """
        Firestore 연결 상태를 확인합니다.
        """
        try:
            if not self.client:
                return False
            
            # 간단한 읽기 작업으로 연결 상태 확인
            test_collection = self.client.collection('_health_check')
            test_doc = test_collection.document('test')
            test_doc.get()
            
            return True
        except Exception as e:
            self.log.warning(f"[DB-firebase]     - Health check failed: {str(e)}")
            return False