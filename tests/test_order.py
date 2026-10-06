"""订单测试（Part 7 重构版）"""
import requests
import pytest


# ==================== 下单成功 ====================

def test_create_order_success(base_url, db, dish_factory, cart_factory):
    """正常下单：订单创建 + 订单项创建 + 购物车清空"""
    # 1. 加两个菜到购物车
    dish_id_1 = dish_factory(name="订单菜1", price=20.1)
    dish_id_2 = dish_factory(name="订单菜2", price=20.2)
    cart_factory(dish_id=dish_id_1, quantity=1)
    cart_factory(dish_id=dish_id_2, quantity=2)

    # 2. 下单
    r = requests.post(f"{base_url}/orders")
    assert r.status_code == 200, f"下单失败：{r.text}"
    order_id = r.json()["data"]["order_id"]
    assert order_id is not None

    # 3. 验证订单主表
    orders = db.execute_query("SELECT * FROM orders WHERE id = ?", (order_id,))
    assert len(orders) == 1
    assert orders[0]["total"] == 20.1 + 20.2 * 2
    assert orders[0]["status"] == "待支付"

    # 4. 验证订单项
    items = db.execute_query("SELECT * FROM order_items WHERE order_id = ?", (order_id,))
    assert len(items) == 2

    # 5. 验证购物车已清空
    cart_rows = db.execute_query("SELECT * FROM cart_items")
    assert len(cart_rows) == 0, "下单后购物车应该清空"


def test_create_order_snapshot(base_url, db, dish_factory, cart_factory):
    """订单存快照：下单后改价，订单价格不变"""
    # 1. 加菜到购物车
    dish_id = dish_factory(name="下单后改价菜", price=38.0)
    cart_factory(dish_id=dish_id, quantity=2)

    # 2. 下单
    r = requests.post(f"{base_url}/orders")
    assert r.status_code == 200
    order_id = r.json()["data"]["order_id"]

    # 3. 改菜品价格
    r_update = requests.put(f"{base_url}/dish/{dish_id}", json={"price": 58.0})
    assert r_update.status_code == 200

    # 4. 验证前置条件：菜品价格确实变了
    dish_rows = db.execute_query("SELECT price FROM dishes WHERE id = ?", (dish_id,))
    assert dish_rows[0]["price"] == 58.0, "前置条件：菜品价格应该已改成 58.0"

    # 5. 验证订单项里的价格还是 38.0（快照）
    item_rows = db.execute_query(
        "SELECT dish_price, total FROM order_items WHERE order_id = ?",
        (order_id,)
    )
    assert item_rows[0]["dish_price"] == 38.0, "订单项价格应该定格在下单时"
    assert item_rows[0]["total"] == 76.0


# ==================== 下单失败 ====================

def test_create_order_empty_cart(base_url, db):
    """购物车为空：不能下单（400）"""
    db.execute_update("DELETE FROM cart_items")

    rows = db.execute_query("SELECT * FROM cart_items")
    assert len(rows) == 0

    r = requests.post(f"{base_url}/orders")
    assert r.status_code == 400


def test_create_order_with_off_shelf_dish(base_url, db, dish_factory, cart_factory):
    """购物车里有下架的菜：不能下单（400）"""
    dish_id = dish_factory(name="下架菜", price=10.0)
    cart_factory(dish_id=dish_id, quantity=1)

    requests.patch(f"{base_url}/dish/{dish_id}/status", json={"status": 0})

    rows = db.execute_query("SELECT status FROM dishes WHERE id = ?", (dish_id,))
    assert rows[0]["status"] == 0

    r = requests.post(f"{base_url}/orders")
    assert r.status_code == 400


def test_create_order_with_soft_deleted_dish(base_url, db, dish_factory, cart_factory):
    """购物车里有软删除的菜：不能下单（400）"""
    dish_id = dish_factory(name="软删除菜", price=10.0)
    cart_factory(dish_id=dish_id, quantity=1)

    requests.delete(f"{base_url}/dish/{dish_id}")

    rows = db.execute_query("SELECT is_deleted FROM dishes WHERE id = ?", (dish_id,))
    assert rows[0]["is_deleted"] == 1

    r = requests.post(f"{base_url}/orders")
    assert r.status_code == 400


def test_create_order_mixed_dishes_fail(base_url, db, dish_factory, cart_factory):
    """购物车里既有正常菜又有软删除菜：整单失败"""
    # 清空订单表（防止前面测试残留）
    db.execute_update("DELETE FROM order_items")
    db.execute_update("DELETE FROM orders")
    db.execute_update("DELETE FROM cart_items")

    # 正常的菜
    normal_dish = dish_factory(name="正常菜", price=10.0)
    cart_factory(dish_id=normal_dish, quantity=1)

    # 软删除的菜
    deleted_dish = dish_factory(name="软删除菜", price=20.0)
    cart_factory(dish_id=deleted_dish, quantity=1)
    requests.delete(f"{base_url}/dish/{deleted_dish}")

    # 下单
    r = requests.post(f"{base_url}/orders")
    assert r.status_code == 400

    # 验证：没有任何订单创建（整单失败）
    orders = db.execute_query("SELECT * FROM orders")
    assert len(orders) == 0, "整单失败后不应该有订单"

    # 验证：购物车没被清空
    cart_rows = db.execute_query("SELECT * FROM cart_items")
    assert len(cart_rows) == 2


# ==================== 查询订单列表 ====================

def test_get_orders_empty(base_url, db):
    """订单列表为空：返回 []"""
    db.execute_update("DELETE FROM order_items")
    db.execute_update("DELETE FROM orders")

    r = requests.get(f"{base_url}/orders")
    assert r.status_code == 200
    assert isinstance(r.json()["data"], list)
    assert len(r.json()["data"]) == 0


def test_get_orders_with_data(base_url, dish_factory, cart_factory, order_factory):
    """订单列表有数据"""
    dish_id = dish_factory(name="订单列表查询菜", price=38.0)
    cart_factory(dish_id=dish_id, quantity=2)
    order_id = order_factory()

    r = requests.get(f"{base_url}/orders")
    assert r.status_code == 200
    data = r.json()["data"]
    assert len(data) >= 1

    # 验证列表里包含这个订单
    ids = [d["id"] for d in data]
    assert order_id in ids

    # 验证按 ID 倒序
    assert ids == sorted(ids, reverse=True)


# ==================== 查询订单详情 ====================

def test_get_order_by_id_success(base_url, dish_factory, cart_factory, order_factory):
    """查看订单详情（包含订单项）"""
    dish_id = dish_factory(name="订单详情查询菜", price=38.0)
    cart_factory(dish_id=dish_id, quantity=2)
    order_id = order_factory()

    r = requests.get(f"{base_url}/orders/{order_id}")
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


def test_get_order_by_id_not_exist(base_url, db):
    """查看不存在的订单：404"""
    rows = db.execute_query("SELECT * FROM orders WHERE id = 99999")
    assert len(rows) == 0

    r = requests.get(f"{base_url}/orders/99999")
    assert r.status_code == 404


# ==================== 订单状态 ====================

def test_order_default_status(base_url, db, dish_factory, cart_factory, order_factory):
    """订单默认状态是'待支付'"""
    dish_id = dish_factory(name="查询状态菜", price=38.0)
    cart_factory(dish_id=dish_id, quantity=1)
    order_id = order_factory()

    rows = db.execute_query("SELECT status FROM orders WHERE id = ?", (order_id,))
    assert rows[0]["status"] == "待支付"