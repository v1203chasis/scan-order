"""用户 CRUD"""
from app.db_helper import execute_update, execute_query
from app.auth import hash_password   # ← 加这行


def create_user(username: str, password: str, role: str = "customer") -> int:
    """创建用户，返回 user_id"""
    """创建用户（密码哈希）"""
    hashed = hash_password(password)   # ← 哈希
    sql = "INSERT INTO users (username, password, role) VALUES (?, ?, ?)"
    return execute_update(sql, (username, hashed, role))


def get_user_by_username(username: str):
    """根据用户名查用户（含密码，用于登录验证）"""
    sql = "SELECT id, username, password, role FROM users WHERE username = ?"
    rows = execute_query(sql, (username,))
    return rows[0] if rows else None


def get_user_by_id(user_id: int):
    """根据 ID 查用户（不含密码，用于返回）"""
    sql = "SELECT id, username, role FROM users WHERE id = ?"
    rows = execute_query(sql, (user_id,))
    return rows[0] if rows else None


def get_all_users():
    """查所有用户"""
    rows = execute_query("SELECT id, username, role FROM users")
    return rows if rows else []


def delete_user(user_id: int) -> bool:
    """删除用户"""
    rows = execute_query("SELECT id FROM users WHERE id = ?", (user_id,))
    if not rows:
        return False
    execute_update("DELETE FROM users WHERE id = ?", (user_id,))
    return True