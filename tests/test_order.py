"""订单测试（Part 7 重构版）"""
import requests
import pytest


# ==================== 下单成功 ====================

def test_create_order_success(base_url, db, dish_factory, cart_factory, customer_ctx):
    """正常下单：订单创建 + 订单项创建 + 购物车清空"""
    user_id, headers = customer_ctx()

    dish_id_1 = dish_factory(name="订单菜1", price=20.1)
    dish_id_2 = dish_factory(name="订单菜2", price=20.2)
    cart_factory(dish_id=dish_id_1, quantity=1, headers=headers)
    cart_factory(dish_id=dish_id_2, quantity=2, headers=headers)

    r = requests.post(f"{base_url}/orders", headers=headers)
    assert r.status_code == 200, f"下单失败：{r.text}"
    order_id = r.json()["data"]["order_id"]
    assert order_id is not None

    orders = db.execute_query(
        "SELECT * FROM orders WHERE id = ? AND user_id = ?",
        (order_id, user_id)
    )
    assert len(orders) == 1
    assert orders[0]["total"] == 20.1 + 20.2 * 2
    assert orders[0]["status"] == "待支付"

    items = db.execute_query("SELECT * FROM order_items WHERE order_id = ?", (order_id,))
    assert len(items) == 2

    cart_rows = db.execute_query("SELECT * FROM cart_items WHERE user_id = ?", (user_id,))
    assert len(cart_rows) == 0


def test_create_order_snapshot(base_url, db, dish_factory, cart_factory, customer_ctx, merchant_ctx):
    """订单存快照：下单后改价，订单价格不变"""
    user_id, headers = customer_ctx()
    _, merchant_h = merchant_ctx()

    dish_id = dish_factory(name="下单后改价菜", price=38.0)
    cart_factory(dish_id=dish_id, quantity=2, headers=headers)

    r = requests.post(f"{base_url}/orders", headers=headers)
    assert r.status_code == 200
    order_id = r.json()["data"]["order_id"]

    r_update = requests.put(f"{base_url}/dish/{dish_id}", json={"price": 58.0}, headers=merchant_h)
    assert r_update.status_code == 200

    dish_rows = db.execute_query("SELECT price FROM dishes WHERE id = ?", (dish_id,))
    assert dish_rows[0]["price"] == 58.0

    item_rows = db.execute_query(
        "SELECT dish_price, total FROM order_items WHERE order_id = ?",
        (order_id,)
    )
    assert item_rows[0]["dish_price"] == 38.0
    assert item_rows[0]["total"] == 76.0


# ==================== 下单失败 ====================

def test_create_order_empty_cart(base_url, db, customer_ctx):
    """购物车为空：不能下单（400）"""
    user_id, headers = customer_ctx()

    cart_rows = db.execute_query("SELECT * FROM cart_items WHERE user_id = ?", (user_id,))
    assert len(cart_rows) == 0

    r = requests.post(f"{base_url}/orders", headers=headers)
    assert r.status_code == 400


def test_create_order_with_off_shelf_dish(base_url, db, dish_factory, cart_factory, customer_ctx, merchant_ctx):
    """购物车里有下架的菜：不能下单（400）"""
    user_id, headers = customer_ctx()
    _, merchant_h = merchant_ctx()

    dish_id = dish_factory(name="下架菜", price=10.0)
    cart_factory(dish_id=dish_id, quantity=1, headers=headers)

    requests.patch(f"{base_url}/dish/{dish_id}/status", json={"status": 0}, headers=merchant_h)

    rows = db.execute_query("SELECT status FROM dishes WHERE id = ?", (dish_id,))
    assert rows[0]["status"] == 0

    r = requests.post(f"{base_url}/orders", headers=headers)
    assert r.status_code == 400


def test_create_order_with_soft_deleted_dish(base_url, db, dish_factory, cart_factory, customer_ctx, merchant_ctx):
    """购物车里有软删除的菜：不能下单（400）"""
    user_id, headers = customer_ctx()
    _, merchant_h = merchant_ctx()

    dish_id = dish_factory(name="软删除菜", price=10.0)
    cart_factory(dish_id=dish_id, quantity=1, headers=headers)

    requests.delete(f"{base_url}/dish/{dish_id}", headers=merchant_h)

    rows = db.execute_query("SELECT is_deleted FROM dishes WHERE id = ?", (dish_id,))
    assert rows[0]["is_deleted"] == 1

    r = requests.post(f"{base_url}/orders", headers=headers)
    assert r.status_code == 400


def test_create_order_mixed_dishes_fail(base_url, db, dish_factory, cart_factory, customer_ctx, merchant_ctx):
    """购物车里既有正常菜又有软删除菜：整单失败"""
    user_id, headers = customer_ctx()
    _, merchant_h = merchant_ctx()

    # 正常的菜
    normal_dish = dish_factory(name="正常菜", price=10.0)
    cart_factory(dish_id=normal_dish, quantity=1, headers=headers)

    # 软删除的菜
    deleted_dish = dish_factory(name="软删除菜", price=20.0)
    cart_factory(dish_id=deleted_dish, quantity=1, headers=headers)
    requests.delete(f"{base_url}/dish/{deleted_dish}", headers=merchant_h)

    # 下单
    r = requests.post(f"{base_url}/orders", headers=headers)
    assert r.status_code == 400

    # 验证：没有订单
    orders = db.execute_query("SELECT * FROM orders WHERE user_id = ?", (user_id,))
    assert len(orders) == 0

    # 验证：购物车没清空
    cart_rows = db.execute_query("SELECT * FROM cart_items WHERE user_id = ?", (user_id,))
    assert len(cart_rows) == 2


# ==================== 查询订单列表 ====================

def test_get_orders_empty(base_url, db, customer_ctx):
    """订单列表为空：返回 []"""
    user_id, headers = customer_ctx()

    r = requests.get(f"{base_url}/orders", headers=headers)
    assert r.status_code == 200
    assert isinstance(r.json()["data"], list)
    assert len(r.json()["data"]) == 0


def test_get_orders_with_data(base_url, dish_factory, cart_factory, customer_ctx):
    """订单列表有数据"""
    user_id, headers = customer_ctx()

    dish_id = dish_factory(name="订单列表查询菜", price=38.0)
    cart_factory(dish_id=dish_id, quantity=2, headers=headers)

    r_create = requests.post(f"{base_url}/orders", headers=headers)
    order_id = r_create.json()["data"]["order_id"]

    r = requests.get(f"{base_url}/orders", headers=headers)
    assert r.status_code == 200
    data = r.json()["data"]
    assert len(data) >= 1

    ids = [d["id"] for d in data]
    assert order_id in ids
    assert ids == sorted(ids, reverse=True)


# ==================== 查询订单详情 ====================

def test_get_order_by_id_success(base_url, dish_factory, cart_factory, customer_ctx):
    """查看订单详情（包含订单项）"""
    user_id, headers = customer_ctx()

    dish_id = dish_factory(name="订单详情查询菜", price=38.0)
    cart_factory(dish_id=dish_id, quantity=2, headers=headers)

    r_create = requests.post(f"{base_url}/orders", headers=headers)
    order_id = r_create.json()["data"]["order_id"]

    r = requests.get(f"{base_url}/orders/{order_id}", headers=headers)
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["id"] == order_id
    assert data["total"] == 76.0
    assert data["status"] == "待支付"
    assert len(data["items"]) == 1
    assert data["items"][0]["dish_name"].startswith("订单详情查询菜")
    assert data["items"][0]["dish_price"] == 38.0
    assert data["items"][0]["quantity"] == 2
    assert data["items"][0]["total"] == 76.0


def test_get_order_by_id_not_exist(base_url, db, customer_ctx):
    """查看不存在的订单：404"""
    user_id, headers = customer_ctx()

    rows = db.execute_query("SELECT * FROM orders WHERE id = 99999")
    assert len(rows) == 0

    r = requests.get(f"{base_url}/orders/99999", headers=headers)
    assert r.status_code == 404


# ==================== 订单状态 ====================

def test_order_default_status(base_url, db, dish_factory, cart_factory, customer_ctx):
    """订单默认状态是'待支付'"""
    user_id, headers = customer_ctx()

    dish_id = dish_factory(name="查询状态菜", price=38.0)
    cart_factory(dish_id=dish_id, quantity=1, headers=headers)

    r = requests.post(f"{base_url}/orders", headers=headers)
    order_id = r.json()["data"]["order_id"]

    rows = db.execute_query("SELECT status FROM orders WHERE id = ?", (order_id,))
    assert rows[0]["status"] == "待支付"