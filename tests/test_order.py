"""订单测试（Part 7）"""
import requests
import pytest

# ==================== 下单成功 ====================
def test_create_order_success(base_url, db, dish_factory, cart_factory, order_factory):
    dish_id_1 = dish_factory(name="订单菜1",price=20.1)
    dish_id_2 = dish_factory(name="订单菜2",price=20.2)

    cart_id_1 = cart_factory(dish_id=dish_id_1,quantity=1)
    cart_id_2 = cart_factory(dish_id=dish_id_2,quantity=2)
    rows = db.execute_query("SELECT * FROM cart_items")
    assert len(rows) >=2

    r = requests.post(f"{base_url}/orders")
    assert r.status_code == 200,f"订单创建失败"
    order_ids = r.json()["data"]["order_ids"]
    assert len(order_ids) >=2

    placeholders = ",".join("?" * len(order_ids))
    rows = db.execute_query(
    f"SELECT * FROM orders WHERE id IN ({placeholders})",
    tuple(order_ids)
    )
    assert len(rows) >= 2

    cart_rows = db.execute_query("SELECT * FROM cart_items")
    assert len(cart_rows) == 0


def test_create_order_snapshot(base_url, db, dish_factory, cart_factory):
    """订单存快照：下单后改价，订单价格不变"""
    # 1. 加菜到购物车
    dish_id = dish_factory(name="价格不变菜", price=38.0)
    cart_factory(dish_id=dish_id, quantity=2)

    r = requests.post(f"{base_url}/orders")
    assert r.status_code == 200
    order_id = r.json()["data"]["order_ids"][0]

    requests.put(f"{base_url}/dish/{dish_id}",json={'price':58.0})
    rows = db.execute_query("SELECT price FROM dishes WHERE id = ?",(dish_id,))
    assert rows[0]["price"] == 58.0

    order_price = db.execute_query("SELECT dish_price,total FROM orders WHERE id = ?",(order_id,))
    assert order_price[0]["dish_price"] == 38.0
    assert order_price[0]["total"] == 76.0


# ==================== 下单失败 ====================

def test_create_order_empty_cart(base_url, db):
    """购物车为空：不能下单（400）"""
    # 清空购物车
    db.execute_update("DELETE FROM cart_items")
    
    # 验证前置条件
    rows = db.execute_query("SELECT * FROM cart_items")
    assert len(rows) ==0

    r = requests.post(f"{base_url}/orders")
    assert r.status_code == 400

def test_create_order_with_off_shelf_dish(base_url, db, dish_factory, cart_factory):
    """购物车里有下架的菜：不能下单（400）"""
    dish_id = dish_factory(name="下架菜", price=10.0)
    cart_factory(dish_id=dish_id, quantity=1)

    # 下架
    requests.patch(f"{base_url}/dish/{dish_id}/status", json={"status": 0})

    # 验证前置条件
    rows = db.execute_query("SELECT status FROM dishes WHERE id = ?", (dish_id,))
    assert rows[0]["status"] == 0, "前置条件：菜品应该已下架"

    # 下单
    r = requests.post(f"{base_url}/orders")
    assert r.status_code == 400, f"下架的菜不能下单：{r.text}"


def test_create_order_with_soft_deleted_dish(base_url, db, dish_factory, cart_factory):
    """购物车里有软删除的菜：不能下单（400）"""
    dish_id = dish_factory(name="软删除菜", price=10.0)
    cart_factory(dish_id=dish_id, quantity=1)

    # 软删除
    requests.delete(f"{base_url}/dish/{dish_id}")

    # 验证前置条件
    rows = db.execute_query("SELECT is_deleted FROM dishes WHERE id = ?", (dish_id,))
    assert rows[0]["is_deleted"] == 1, "前置条件：菜品应该已软删除"

    # 下单
    r = requests.post(f"{base_url}/orders")
    assert r.status_code == 400, f"软删除的菜不能下单：{r.text}"



# ==================== 查询订单列表 ====================

def test_get_orders_empty(base_url, db):
    """订单列表为空：返回 []"""
    # 清空订单
    db.execute_update("DELETE FROM orders")
    
    r = requests.get(f"{base_url}/orders")
    assert r.status_code == 200
    assert isinstance(r.json()["data"], list)
    assert len(r.json()["data"]) == 0


def test_get_orders_with_data(base_url, db, dish_factory, cart_factory, order_factory):
    """订单列表有数据"""
    dish_id = dish_factory(name="宫保鸡丁", price=38.0)
    cart_factory(dish_id=dish_id, quantity=2)
    order_ids = order_factory()
    
    r = requests.get(f"{base_url}/orders")
    assert r.status_code == 200
    data = r.json()["data"]
    assert len(data) >= 1
    
    # 验证最新订单在前面（ORDER BY id DESC）
    ids = [d["id"] for d in data]
    assert ids == sorted(ids, reverse=True), "订单应该按 id 倒序排列"


# ==================== 查询订单详情 ====================

def test_get_order_by_id_success(base_url, db, dish_factory, cart_factory, order_factory):
    """查看订单详情成功"""
    dish_id = dish_factory(name="订单详情菜", price=38.0)
    cart_factory(dish_id=dish_id, quantity=2)
    order_ids = order_factory()
    
    r = requests.get(f"{base_url}/orders/{order_ids[0]}")
    assert r.status_code == 200
    assert r.json()["data"]["dish_name"].startswith("订单详情菜")
    assert r.json()["data"]["dish_price"] == 38.0
    assert r.json()["data"]["quantity"] == 2
    assert r.json()["data"]["total"] == 76.0


def test_get_order_by_id_not_exist(base_url, db):
    """查看不存在的订单：404"""
    # 验证前置条件
    rows = db.execute_query("SELECT * FROM orders WHERE id = 99999")
    assert len(rows) == 0

    r = requests.get(f"{base_url}/orders/99999")
    assert r.status_code == 404


# ==================== 订单状态 ====================

def test_order_default_status(base_url, db, dish_factory, cart_factory, order_factory):
    """订单默认状态是'待支付'"""
    dish_id = dish_factory(name="支付状态菜", price=38.0)
    cart_factory(dish_id=dish_id, quantity=1)
    order_ids = order_factory()

    rows = db.execute_query("SELECT status FROM orders WHERE id = ?", (order_ids[0],))
    assert rows[0]["status"] == "待支付", f"默认状态应该是'待支付'，实际是 {rows[0]['status']}"