# app/config.py
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def get_db_path():
    return os.getenv("DB_PATH", str(BASE_DIR / "scan_order.db"))


def get_base_url():
    return os.getenv("BASE_URL", "http://127.0.0.1:8000")


def get_secret_key():
    return os.getenv("SECRET_KEY", "dev-secret-key")




'''
流程
1. 你手动设 $env:DB_PATH = "test_scan_order.db"
   ↓
2. config.py 用 os.getenv("DB_PATH") 读出你的输入
   ↓
3. config.DB_PATH = "test_scan_order.db"
   ↓
4. db_helper.py 用 from app.config import config，拿到 DB_PATH
   ↓
5. 数据库操作都用 test_scan_order.db
'''

# ================= 新增部分 =================
class Config:
    @property#
    def SECRET_KEY(self):
        return get_secret_key()
    
    @property
    def DB_PATH(self):
        return get_db_path()
    
    @property
    def BASE_URL(self):
        return get_base_url()
    
    @property
    def ALGORITHM(self):
        return os.getenv("ALGORITHM", "HS256")

# 实例化并暴露出去
config = Config()
# ============================================