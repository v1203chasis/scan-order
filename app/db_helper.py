import sqlite3
from app.config import get_db_path


def get_conn():
    conn = sqlite3.connect(get_db_path(), isolation_level=None)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """启动时建表，存在则跳过"""
    with get_conn() as conn:
        conn.execute("PRAGMA journal_mode=WAL")

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
                user_id INTEGER NOT NULL,  
                dish_id INTEGER NOT NULL UNIQUE,
                quantity INTEGER NOT NULL DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (user_id, dish_id)
            );
        """)

        # 3. 建 orders 表
        conn.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,   -- ← 加
            total REAL NOT NULL,
            status TEXT NOT NULL DEFAULT '待支付',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # 4. 建 order_items 表
        conn.execute("""
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                dish_id INTEGER NOT NULL,
                dish_name TEXT NOT NULL,
                dish_price REAL NOT NULL,
                quantity INTEGER NOT NULL,
                total REAL NOT NULL
            )
        """)

        # 5. 建 payments 表
        conn.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                method TEXT NOT NULL DEFAULT '模拟支付',
                status TEXT NOT NULL DEFAULT '待支付',
                transaction_id TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'customer'
            );

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