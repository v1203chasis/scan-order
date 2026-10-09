"""集中管理配置"""
import os
from pathlib import Path


class Config:
    # 项目根目录
    BASE_DIR = Path(__file__).resolve().parent.parent

    # 数据库路径（支持环境变量切换）
    DB_PATH = os.getenv("DB_PATH", str(BASE_DIR / "scan_order.db"))

    # 服务地址
    BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000")

    # 密钥（Part 11 用）
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")

    # 支付方式
    PAYMENT_METHOD = os.getenv("PAYMENT_METHOD", "模拟支付")


# 全局配置实例
config = Config()

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