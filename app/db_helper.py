import sqlite3
from pathlib import Path

# 数据库文件放在项目根目录
DB_PATH = Path(__file__).resolve().parent.parent / "scan_order.db"


def get_conn():
    conn = sqlite3.connect("scan_order.db", isolation_level=None)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """启动时建表，存在则跳过"""
    with get_conn() as conn:
        # 1. 建 dishes 表
        conn.execute("""
            CREATE TABLE IF NOT EXISTS dishes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                status INTEGER NOT NULL DEFAULT 1,
                is_deleted INTEGER NOT NULL DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_dishes_status ON dishes(status)")

        # 2. 建 cart_items 表
        conn.execute("""
            CREATE TABLE IF NOT EXISTS cart_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dish_id INTEGER NOT NULL UNIQUE,
                quantity INTEGER NOT NULL DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 3. 建 orders 表（新增）
        conn.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dish_id INTEGER NOT NULL,
                dish_name TEXT NOT NULL,
                dish_price REAL NOT NULL,
                quantity INTEGER NOT NULL,
                total REAL NOT NULL,
                status TEXT NOT NULL DEFAULT '待支付',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()


def execute_query(sql: str, params: tuple = ()):
    """查询，返回 list[dict]"""
    with get_conn() as conn:
        cursor = conn.execute(sql, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def execute_update(sql: str, params: tuple = ()):
    """增删改，返回 lastrowid（INSERT）或影响行数（UPDATE/DELETE）"""
    with get_conn() as conn:
        cursor = conn.execute(sql, params)
        conn.commit()
        if sql.strip().upper().startswith("INSERT"):
            return cursor.lastrowid
        return cursor.rowcount

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")   # ← 加这一行
    return conn