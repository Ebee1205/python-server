# py_server.py
import asyncio
import signal
import sys
import os

# 현재 스크립트의 부모 디렉토리를 sys.path에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from src.app_context import AppContext

class PythonServer:
    def __init__(self):
        self.ctx = AppContext()
        self.running = False
        self.background_tasks = []
        
    async def initialize(self):
        """서버 초기화"""
        try:
            print("     - Initializing application...")
            
            # 설정 로드
            self.ctx.load_config("src/service/conf/ankoko-ai-server-local.cfg.json")
            
            # logger 초기화
            self.ctx._init_logger()
            self.test_logging(self.ctx.log)

            # 매니저 초기화
            self.ctx._init_system_manager()
            
            # 핸들러 초기화
            self.ctx._init_websocket()
            self.ctx._init_redis()
            self.ctx._init_rmq()

            # 알고리즘 초기화
            self.ctx._init_llms()

            # 연결 시작
            await self.ctx.rmq_handler.connect()
            await self.ctx.rmq_handler.consume_multi()
            await self.ctx.redis_handler.connect()

            self.ctx.log.info("     == Initialization complete")
            self.running = True
            
        except Exception as e:
            self.ctx.log.error(f"     -- Initialization error: {str(e)}")
            import traceback
            traceback.print_exc()
            raise

    async def start_background_tasks(self):
        """백그라운드 작업들 시작"""
        # 주기적으로 실행할 작업들을 태스크로 등록
        self.background_tasks.extend([
            asyncio.create_task(self.periodic_health_check()),
            asyncio.create_task(self.periodic_cleanup()),
            # 필요한 다른 백그라운드 작업들 추가
        ])
        
        self.ctx.log.info("     -- Background tasks started")

    async def periodic_cleanup(self):
        """주기적 정리 작업"""
        while self.running:
            try:
                # 메모리 정리, 세션 정리 등
                await asyncio.sleep(300)  # 5분마다 실행
            except Exception as e:
                self.ctx.log.error(f"Cleanup error: {e}")

    async def shutdown(self):
        """서버 종료"""
        if not self.running:
            return
            
        self.running = False
        
        if self.ctx.log:
            self.ctx.log.info("     -- Shutting down application")

        # 백그라운드 태스크 종료
        for task in self.background_tasks:
            task.cancel()
        
        if self.background_tasks:
            await asyncio.gather(*self.background_tasks, return_exceptions=True)
            self.ctx.log.info("     -- Background tasks stopped")

        # 핸들러들 종료 (역순)
        if self.ctx.redis_handler:
            try:
                await self.ctx.redis_handler.disconnect()
                self.ctx.log.info("     -- Redis handler closed")
            except Exception as e:
                self.ctx.log.warning(f"     - Redis close failed: {e}")
        
        if self.ctx.ws_handler:
            try:
                await self.ctx.ws_handler.disconnect_all()
                self.ctx.log.info("     -- WebSocket handler closed")
            except Exception as e:
                self.ctx.log.warning(f"     - WebSocket close failed: {e}")

        if self.ctx.rmq_handler:
            try:
                await self.ctx.rmq_handler.disconnect()
                self.ctx.log.info("     -- RabbitMQ handler closed")
            except Exception as e:
                self.ctx.log.warning(f"     - RabbitMQ close failed: {e}")

        if self.ctx.system_monitor:
            try:
                self.ctx.system_monitor.stop()
                self.ctx.log.info("     -- system monitor stopped")
            except Exception as e:
                self.ctx.log.warning(f"     - system monitor stop failed: {e}")

        # LLM 모델 정리
        if hasattr(self.ctx, "llm_models") and self.ctx.llm_models:
            try:
                for name, model in self.ctx.llm_models.items():
                    self.ctx.log.info(f"     -- LLM model '{name}' unloaded (model={getattr(model, 'model', 'unknown')})")
                self.ctx.llm_models.clear()
            except Exception as e:
                self.ctx.log.warning(f"     - LLM models cleanup failed: {e}")

        self.ctx.log.info("     -- Server shutdown complete")

    def test_logging(self, logger):
        """로깅 테스트"""
        logger.info("-- FILE LOG TEST START --")
        logger.debug("   -test debug level")
        logger.info("    -test info level")
        logger.warning(" -test warn level")
        logger.error("   -test error level")
        logger.info("-- FILE LOG TEST END --")

    async def run(self):
        """메인 서버 실행 루프"""
        await self.initialize()
        await self.start_background_tasks()
        
        try:
            self.ctx.log.info("     == Server is running...")
            self.ctx.log.info("     -- Press Ctrl+C to stop")
            
            # 무한 루프로 서버 유지
            while self.running:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            self.ctx.log.info("     -- Received interrupt signal")
        except Exception as e:
            self.ctx.log.error(f"     -- Server error: {str(e)}")
            import traceback
            traceback.print_exc()
        finally:
            await self.shutdown()


def handle_signal(signum, frame):
    """시그널 핸들러"""
    print(f"     -- Received signal {signum}")
    loop = asyncio.get_event_loop()
    if loop.is_running():
        loop.create_task(server.shutdown())


if __name__ == "__main__":
    try:
        server = PythonServer()
        
        # 시그널 핸들러 등록
        signal.signal(signal.SIGINT, handle_signal)
        signal.signal(signal.SIGTERM, handle_signal)
        
        asyncio.run(server.run())

    except KeyboardInterrupt:
        print("\n     -- Server stopped")

    except Exception as e:
        print(f"     -- Fatal error: {str(e)}")
        sys.exit(1)

# 실행코드
# python src/py_server_mw.py