"""支付测试（Part 8）"""
import requests
import pytest


# ==================== 支付成功 ====================
def test_pay_order_amount_match(base_url, db, dish_factory, cart_factory, order_factory):
    """多菜品组合：支付金额 = 订单总价"""
    dish_id_1 = dish_factory(name="菜1", price=20.5)   # 小数
    dish_id_2 = dish_factory(name="菜2", price=30.3)
    dish_id_3 = dish_factory(name="菜3", price=15.7)
    cart_factory(dish_id=dish_id_1, quantity=2)   # 41.0
    cart_factory(dish_id=dish_id_2, quantity=1)   # 30.3
    cart_factory(dish_id=dish_id_3, quantity=3)   # 47.1
    order_id = order_factory()

    # 订单总价 = 41.0 + 30.3 + 47.1 = 118.4
    orders = db.execute_query("SELECT total FROM orders WHERE id = ?", (order_id,))
    assert orders[0]["total"] == pytest.approx(118.4)   # ← 用 approx，浮点数精度问题
    #assert orders[0]["total"] == 118.4

    # 支付
    r = requests.post(f"{base_url}/orders/{order_id}/pay")
    assert r.status_code == 200
    payment_id = r.json()["data"]["payment_id"]

    # 验证支付金额
    payments = db.execute_query("SELECT amount FROM payments WHERE id = ?", (payment_id,))
    assert payments[0]["amount"] == pytest.approx(118.4)   # ← 用 approx
    #assert payments[0]["amount"] == 118.4


# ==================== 支付失败 ====================

def test_pay_order_not_exist(base_url, db):
    """支付不存在的订单：400"""
    rows = db.execute_query("SELECT * FROM orders WHERE id = 99999")
    assert len(rows) == 0

    r = requests.post(f"{base_url}/orders/99999/pay")
    assert r.status_code == 400


def test_pay_order_twice(base_url, db, dish_factory, cart_factory, order_factory):
    """重复支付：幂等，第二次返回 400"""
    dish_id = dish_factory(name="重复支付菜", price=38.0)
    cart_factory(dish_id=dish_id, quantity=2)
    order_id = order_factory()

    # 第一次支付成功
    r1 = requests.post(f"{base_url}/orders/{order_id}/pay")
    assert r1.status_code == 200
    payment_id_1 = r1.json()["data"]["payment_id"]

    # 第二次支付应该 400
    r2 = requests.post(f"{base_url}/orders/{order_id}/pay")
    assert r2.status_code == 400, f"重复支付应该返回 400：{r2.text}"

    # 验证：只有一条支付记录
    payments = db.execute_query("SELECT * FROM payments WHERE order_id = ?", (order_id,))
    assert len(payments) == 1, "重复支付不应该产生新记录"

    # 验证：订单状态还是"已支付"
    orders = db.execute_query("SELECT status FROM orders WHERE id = ?", (order_id,))
    assert orders[0]["status"] == "已支付"


# ==================== 查询支付记录 ====================

def test_get_payment_by_id_success(base_url, db, dish_factory, cart_factory, order_factory):
    """按支付 ID 查成功"""
    dish_id = dish_factory(name="查询支付ID菜", price=38.0)
    cart_factory(dish_id=dish_id, quantity=2)
    order_id = order_factory()

    r_pay = requests.post(f"{base_url}/orders/{order_id}/pay")
    payment_id = r_pay.json()["data"]["payment_id"]

    r = requests.get(f"{base_url}/payments/{payment_id}")
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["id"] == payment_id
    assert data["order_id"] == order_id
    assert data["amount"] == 76.0
    assert data["status"] == "支付成功"
    assert data["method"] == "模拟支付"


def test_get_payment_by_id_not_exist(base_url, db):
    """按支付 ID 查不存在：404"""
    rows = db.execute_query("SELECT * FROM payments WHERE id = 99999")
    assert len(rows) == 0

    r = requests.get(f"{base_url}/payments/99999")
    assert r.status_code == 404


def test_get_payments_by_order(base_url, db, dish_factory, cart_factory, order_factory):
    """按订单 ID 查所有支付记录"""
    dish_id = dish_factory(name="订单id查询菜", price=38.0)
    cart_factory(dish_id=dish_id, quantity=2)
    order_id = order_factory()

    # 支付
    r_pay = requests.post(f"{base_url}/orders/{order_id}/pay")
    payment_id = r_pay.json()["data"]["payment_id"]

    # 查支付记录
    r = requests.get(f"{base_url}/orders/{order_id}/payments")
    assert r.status_code == 200
    data = r.json()["data"]
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["id"] == payment_id
    assert data[0]["order_id"] == order_id


def test_get_payments_by_order_empty(base_url, db):
    """按订单 ID 查（无记录）：返回 []"""
    # 确保这个订单没有支付记录
    rows = db.execute_query("SELECT * FROM payments WHERE order_id = 99999")
    assert len(rows) == 0

    r = requests.get(f"{base_url}/orders/99999/payments")
    assert r.status_code == 200
    assert isinstance(r.json()["data"], list)
    assert len(r.json()["data"]) == 0