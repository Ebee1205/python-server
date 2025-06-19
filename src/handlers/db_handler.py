# db_handler.py

import pymysql
from pymysql.connections import Connection
import threading

class DBHandler:
    def __init__(self, ctx):
        self.ctx = ctx
        self.log = ctx.log
        
        self.connection = None
        self.lock = threading.Lock()

    def connect(self):
        try:
            conf = self.ctx.cfg.db_config
            self.connection = pymysql.connect(
                host=conf.host,
                port=conf.port,
                user=conf.user,
                password=conf.password,
                database=conf.database,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=True
            )
            self.log.info("DB", "++ Connected (host=%s, db=%s)", conf.host, conf.database)
        except Exception as e:
            self.log.error("DB", "- Connection error: %s", str(e))
            self.connection = None

    def get_connection(self) -> Connection:
        with self.lock:
            if self.connection is None or not self.connection.open:
                self.log.warning("DB", "- not connected")
                self.connect()
            return self.connection

    def disconnect(self):
        with self.lock:
            if self.connection:
                try:
                    self.connection.close()
                    self.log.info("DB", "-- Disconnected")
                except Exception as e:
                    self.log.warning("DB", "- Disconnect failed: %s", str(e))
                finally:
                    self.connection = None
    
    def get_cursor(self):
        return DBCursor(self)


class DBCursor:
    def __init__(self, db_handler, log):
        self.db_handler = db_handler
        self.log = log
        self.cursor = None

    def __enter__(self):
        try:
            conn = self.db_handler.get_connection()
            self.cursor = conn.cursor()
            return self.cursor
        except Exception as e:
            self.log.error("DB", "- Acquire Cursor Failed: %s", str(e))
            raise

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.cursor:
            try:
                self.cursor.close()
            except Exception as e:
                self.log.warning("DB", "- Close Cursor Failed: %s", str(e))