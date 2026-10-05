"""订单 CRUD"""
from app.db_helper import execute_query, execute_update, get_conn


def create_order_from_cart():
    """
    从购物车创建订单（事务）
    返回：订单 ID 列表，或 None（购物车为空 / 有菜不能下单）
    """
    # 1. 查购物车
    cart_items = execute_query("""
        SELECT ci.dish_id, ci.quantity, d.name, d.price, d.status, d.is_deleted
        FROM cart_items ci
        LEFT JOIN dishes d ON ci.dish_id = d.id
    """)
    if not cart_items:
        return None   # 购物车为空

    # 2. 校验每个菜是否能下单（有一个失败了整单都不能下单！）
    for item in cart_items:
        if item["name"] is None:
            return None   # 菜品被硬删除
        if item["is_deleted"] == 1:
            return None   # 菜品被软删除
        if item["status"] != 1:
            return None   # 菜品已下架

    # 3. 事务：创建订单 + 清空购物车
    with get_conn() as conn:
        try:
            conn.execute("BEGIN")
            order_ids = []
            for item in cart_items:
                total = item["price"] * item["quantity"]
                cursor = conn.execute(
                    """
                    INSERT INTO orders (dish_id, dish_name, dish_price, quantity, total)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (item["dish_id"], item["name"], item["price"], item["quantity"], total)
                )
                order_ids.append(cursor.lastrowid)
            # 清空购物车
            conn.execute("DELETE FROM cart_items")
            conn.commit()
            return order_ids
        except Exception as e:
            conn.rollback()
            raise e


def get_orders():
    """查看订单列表"""
    rows = execute_query(
        "SELECT id, dish_id, dish_name, dish_price, quantity, total, status, created_at FROM orders ORDER BY id DESC"
    )
    return rows if rows else []
#这个是用户打开我的订单页面，查看所有订单

def get_order_by_id(order_id: int):
    """查看订单详情"""
    rows = execute_query(
        "SELECT id, dish_id, dish_name, dish_price, quantity, total, status, created_at FROM orders WHERE id = ?",
        (order_id,)
    )
    return rows[0] if rows else None
#这个是用户在所有订单中点击某条进入详情


