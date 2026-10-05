from app.db_helper import execute_update, execute_query

# crud_cart.py
def add_to_cart(dish_id, quantity):
    """加入购物车（已存在则累加）"""
    # 1. 校验菜品是否存在、上架、未软删除
    dish = execute_query(
        "SELECT id FROM dishes WHERE id = ? AND is_deleted = 0 AND status = 1",
        (dish_id,)
    )
    if not dish:
        return None   # 菜品不存在、已下架、已软删除
    
    # 2. 检查购物车里是否已有这个菜
    rows = execute_query("SELECT id, quantity FROM cart_items WHERE dish_id = ?", (dish_id,))
    if rows:
        # 累加数量
        cart_id = rows[0]["id"]
        new_quantity = rows[0]["quantity"] + quantity
        execute_update("UPDATE cart_items SET quantity = ? WHERE id = ?", (new_quantity, cart_id))
        return cart_id
    else:
        # 新增
        execute_update("INSERT INTO cart_items (dish_id, quantity) VALUES (?, ?)", (dish_id, quantity))
        new_rows = execute_query("SELECT id FROM cart_items WHERE dish_id = ?", (dish_id,))
        return new_rows[0]["id"]


def get_cart_items():
    """查看购物车（关联菜品信息）"""
    sql = """
        SELECT ci.id AS cart_id, ci.dish_id, ci.quantity, d.name, d.price, d.status, d.is_deleted
        FROM cart_items ci
        LEFT JOIN dishes d ON ci.dish_id = d.id
    """
    rows = execute_query(sql)
    return rows if rows else []


def update_cart_quantity(cart_id, quantity):
    """改数量"""
    rows = execute_query("SELECT id FROM cart_items WHERE id = ?", (cart_id,))
    if not rows:
        return False
    
    execute_update("UPDATE cart_items SET quantity = ? WHERE id = ?", (quantity, cart_id))
    return True


def delete_cart_item(cart_id):
    """删除"""
    rows = execute_query("SELECT id FROM cart_items WHERE id = ?", (cart_id,))
    if not rows:
        return False
    execute_update("DELETE FROM cart_items WHERE id = ?", (cart_id,))
    return True

