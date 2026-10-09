"""支付测试（Part 8）"""
import requests
import pytest


# ==================== 支付成功 ====================

def test_pay_order_amount_match(base_url, db, dish_factory, cart_factory, customer_ctx):
    """多菜品组合：支付金额 = 订单总价"""
    user_id, headers = customer_ctx()

    # 1. 加 3 个菜到购物车
    dish_id_1 = dish_factory(name="菜1", price=20.5)
    dish_id_2 = dish_factory(name="菜2", price=30.3)
    dish_id_3 = dish_factory(name="菜3", price=15.7)
    cart_factory(dish_id=dish_id_1, quantity=2, headers=headers)   # 41.0
    cart_factory(dish_id=dish_id_2, quantity=1, headers=headers)   # 30.3
    cart_factory(dish_id=dish_id_3, quantity=3, headers=headers)   # 47.1

    # 2. 下单
    r_create = requests.post(f"{base_url}/orders", headers=headers)
    order_id = r_create.json()["data"]["order_id"]

    # 3. 验证订单总价（用 user_id 定位）
    orders = db.execute_query(
        "SELECT total FROM orders WHERE id = ? AND user_id = ?",
        (order_id, user_id)
    )
    assert orders[0]["total"] == pytest.approx(118.4)

    # 4. 支付
    r = requests.post(f"{base_url}/orders/{order_id}/pay", headers=headers)
    assert r.status_code == 200, f"支付失败：{r.text}"
    payment_id = r.json()["data"]["payment_id"]

    # 5. 验证支付金额
    payments = db.execute_query("SELECT amount FROM payments WHERE id = ?", (payment_id,))
    assert payments[0]["amount"] == pytest.approx(118.4)


# ==================== 支付失败 ====================

def test_pay_order_not_exist(base_url, db, customer_ctx):
    """支付不存在的订单：400"""
    user_id, headers = customer_ctx()

    rows = db.execute_query("SELECT * FROM orders WHERE id = 99999")
    assert len(rows) == 0

    r = requests.post(f"{base_url}/orders/99999/pay", headers=headers)
    assert r.status_code == 400


def test_pay_order_twice(base_url, db, dish_factory, cart_factory, customer_ctx):
    """重复支付：幂等，第二次返回 400"""
    user_id, headers = customer_ctx()

    dish_id = dish_factory(name="重复支付菜", price=38.0)
    cart_factory(dish_id=dish_id, quantity=2, headers=headers)

    r_create = requests.post(f"{base_url}/orders", headers=headers)
    order_id = r_create.json()["data"]["order_id"]

    # 第一次支付成功
    r1 = requests.post(f"{base_url}/orders/{order_id}/pay", headers=headers)
    assert r1.status_code == 200

    # 第二次支付应该 400
    r2 = requests.post(f"{base_url}/orders/{order_id}/pay", headers=headers)
    assert r2.status_code == 400

    # 验证：只有一条支付记录
    payments = db.execute_query("SELECT * FROM payments WHERE order_id = ?", (order_id,))
    assert len(payments) == 1

    # 验证：订单状态还是"已支付"
    orders = db.execute_query(
        "SELECT status FROM orders WHERE id = ? AND user_id = ?",
        (order_id, user_id)
    )
    assert orders[0]["status"] == "已支付"


# ==================== 查询支付记录 ====================

def test_get_payment_by_id_success(base_url, db, dish_factory, cart_factory, customer_ctx):
    """按支付 ID 查成功"""
    user_id, headers = customer_ctx()

    dish_id = dish_factory(name="查询支付ID菜", price=38.0)
    cart_factory(dish_id=dish_id, quantity=2, headers=headers)

    r_create = requests.post(f"{base_url}/orders", headers=headers)
    order_id = r_create.json()["data"]["order_id"]

    r_pay = requests.post(f"{base_url}/orders/{order_id}/pay", headers=headers)
    payment_id = r_pay.json()["data"]["payment_id"]

    r = requests.get(f"{base_url}/payments/{payment_id}", headers=headers)
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["id"] == payment_id
    assert data["order_id"] == order_id
    assert data["amount"] == 76.0
    assert data["status"] == "支付成功"
    assert data["method"] == "模拟支付"


def test_get_payment_by_id_not_exist(base_url, db, customer_ctx):
    """按支付 ID 查不存在：404"""
    user_id, headers = customer_ctx()

    rows = db.execute_query("SELECT * FROM payments WHERE id = 99999")
    assert len(rows) == 0

    r = requests.get(f"{base_url}/payments/99999", headers=headers)
    assert r.status_code == 404


def test_get_payments_by_order(base_url, db, dish_factory, cart_factory, customer_ctx):
    """按订单 ID 查所有支付记录"""
    user_id, headers = customer_ctx()

    dish_id = dish_factory(name="订单id查询菜", price=38.0)
    cart_factory(dish_id=dish_id, quantity=2, headers=headers)

    r_create = requests.post(f"{base_url}/orders", headers=headers)
    order_id = r_create.json()["data"]["order_id"]

    r_pay = requests.post(f"{base_url}/orders/{order_id}/pay", headers=headers)
    payment_id = r_pay.json()["data"]["payment_id"]

    r = requests.get(f"{base_url}/orders/{order_id}/payments", headers=headers)
    assert r.status_code == 200
    data = r.json()["data"]
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["id"] == payment_id
    assert data[0]["order_id"] == order_id


def test_get_payments_by_order_empty(base_url, db, customer_ctx):
    """按订单 ID 查（无记录）：返回 []"""
    user_id, headers = customer_ctx()

    rows = db.execute_query("SELECT * FROM payments WHERE order_id = 99999")
    assert len(rows) == 0

    r = requests.get(f"{base_url}/orders/99999/payments", headers=headers)
    assert r.status_code == 200
    assert isinstance(r.json()["data"], list)
    assert len(r.json()["data"]) == 0