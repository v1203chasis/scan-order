"""订单 CRUD"""
from app.db_helper import execute_query, execute_update, get_conn


def create_order_from_cart():
    """
    从购物车创建订单（事务）
    返回：订单 ID，或 None（购物车为空 / 有菜不能下单）
    """
    # 1. 查购物车
    cart_items = execute_query("""
        SELECT ci.dish_id, ci.quantity, d.name, d.price, d.status, d.is_deleted
        FROM cart_items ci
        LEFT JOIN dishes d ON ci.dish_id = d.id
    """)
    if not cart_items:
        return None

    # 2. 校验每个菜是否能下单
    for item in cart_items:
        if item["name"] is None:
            return None
        if item["is_deleted"] == 1:
            return None
        if item["status"] != 1:
            return None

    # 3. 计算订单总价
    total = sum(item["price"] * item["quantity"] for item in cart_items)

    # 4. 事务：创建订单 + 订单项 + 清空购物车
    with get_conn() as conn:
        try:
            conn.execute("BEGIN")

            # 4.1 创建订单主表记录（只 INSERT 一次）
            cursor = conn.execute(
                "INSERT INTO orders (total) VALUES (?)",
                (total,)
            )
            order_id = cursor.lastrowid   # 订单号（只有一个）

            # 4.2 创建订单项（每个菜 INSERT 一次）
            for item in cart_items:
                item_total = item["price"] * item["quantity"]
                conn.execute(
                    """
                    INSERT INTO order_items (order_id, dish_id, dish_name, dish_price, quantity, total)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (order_id, item["dish_id"], item["name"], item["price"], item["quantity"], item_total)
                )

            # 4.3 清空购物车
            conn.execute("DELETE FROM cart_items")
            conn.commit()
            return order_id   # ← 返回单个订单号，不是列表
        except Exception as e:
            conn.rollback()
            raise e


def get_orders():
    """查看订单列表"""
    rows = execute_query(
        "SELECT id, total, status, created_at FROM orders ORDER BY id DESC"
    )
    return rows if rows else []
#这个是用户打开我的订单页面，查看所有订单

def get_order_by_id(order_id: int):
    """查看订单详情（包含订单项）"""
    # 1. 查订单主表
    order_rows = execute_query(
        "SELECT id, total, status, created_at FROM orders WHERE id = ?",
        (order_id,)
    )
    if not order_rows:
        return None
    #前置条件：就是这个订单存不存在

    order = order_rows[0]
    #execute.query的返回都是字典列表，所以要取值就要把列表先去掉（拿出字典）
    
    # 2. 查订单项
    item_rows = execute_query(
        "SELECT id, dish_id, dish_name, dish_price, quantity, total FROM order_items WHERE order_id = ?",
        (order_id,)
    )
    order["items"] = item_rows if item_rows else []#这个是values，然后【】这里是防御性编程
    #order里面并没有item这个key，所以这里是动态添加，往order = order_rows[0]里面加上这个key以及它的values
    
    return order
#这个是用户在所有订单中点击某条进入详情
'''
返回的order
{
    "id": 1,
    "total": 162.0,
    "status": "待支付",
    "created_at": "2024-01-01 12:00:00",
    "items": [
        {"id": 1, "dish_id": 5, "dish_name": "宫保鸡丁", "dish_price": 38.0, "quantity": 2, "total": 76.0},
        {"id": 2, "dish_id": 8, "dish_name": "麻婆豆腐", "dish_price": 28.0, "quantity": 1, "total": 28.0},
        {"id": 3, "dish_id": 12, "dish_name": "水煮牛肉", "dish_price": 58.0, "quantity": 1, "total": 58.0}
    ]
}

'''


