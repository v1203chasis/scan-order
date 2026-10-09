"""订单状态流转测试（Part 9）"""
import requests
import pytest


# ==================== 辅助函数（统一 6 个参数） ====================

def create_pending_order(dish_factory, cart_factory, order_factory, base_url, headers, merchant_h):
    """创建一个待支付的订单，返回 order_id"""
    dish_id = dish_factory(name="测试菜", price=20.0)
    cart_factory(dish_id=dish_id, quantity=1, headers=headers)
    return order_factory(headers=headers)


def create_paid_order(dish_factory, cart_factory, order_factory, base_url, headers, merchant_h):
    """创建一个已支付的订单，返回 order_id"""
    order_id = create_pending_order(dish_factory, cart_factory, order_factory, base_url, headers, merchant_h)
    r = requests.post(f"{base_url}/orders/{order_id}/pay", headers=headers)
    assert r.status_code == 200, f"辅助：支付失败 {r.text}"
    return order_id


def create_accepted_order(dish_factory, cart_factory, order_factory, base_url, headers, merchant_h):
    """创建一个已接单的订单，返回 order_id"""
    order_id = create_paid_order(dish_factory, cart_factory, order_factory, base_url, headers, merchant_h)
    r = requests.post(f"{base_url}/orders/{order_id}/accept", headers=merchant_h)   # ← 商户 token
    assert r.status_code == 200, f"辅助：接单失败 {r.text}"
    return order_id


def create_completed_order(dish_factory, cart_factory, order_factory, base_url, headers, merchant_h):
    """创建一个已完成的订单，返回 order_id"""
    order_id = create_accepted_order(dish_factory, cart_factory, order_factory, base_url, headers, merchant_h)
    r = requests.post(f"{base_url}/orders/{order_id}/complete", headers=merchant_h)   # ← 商户 token
    assert r.status_code == 200, f"辅助：完成失败 {r.text}"
    return order_id


def create_cancelled_order(dish_factory, cart_factory, order_factory, base_url, headers, merchant_h):
    """创建一个已取消的订单，返回 order_id"""
    order_id = create_pending_order(dish_factory, cart_factory, order_factory, base_url, headers, merchant_h)
    r = requests.post(f"{base_url}/orders/{order_id}/cancel", headers=headers)
    assert r.status_code == 200, f"辅助：取消失败 {r.text}"
    return order_id


def create_refunded_order(dish_factory, cart_factory, order_factory, base_url, headers, merchant_h):
    """创建一个已退款的订单，返回 order_id"""
    order_id = create_paid_order(dish_factory, cart_factory, order_factory, base_url, headers, merchant_h)
    r = requests.post(f"{base_url}/orders/{order_id}/refund", headers=headers)
    assert r.status_code == 200, f"辅助：退款失败 {r.text}"
    return order_id


# ==================== 取消订单 ====================

def test_cancel_pending_order(base_url, db, dish_factory, cart_factory, customer_ctx, merchant_ctx, order_factory):
    """取消待支付的订单：成功"""
    user_id, headers = customer_ctx()
    _, merchant_h = merchant_ctx()

    order_id = create_pending_order(dish_factory, cart_factory, order_factory, base_url, headers, merchant_h)

    rows = db.execute_query("SELECT status FROM orders WHERE id = ?", (order_id,))
    assert rows[0]["status"] == "待支付"

    r = requests.post(f"{base_url}/orders/{order_id}/cancel", headers=headers)
    assert r.status_code == 200, f"取消失败：{r.text}"

    rows = db.execute_query("SELECT status FROM orders WHERE id = ?", (order_id,))
    assert rows[0]["status"] == "已取消"


@pytest.mark.parametrize("create_fn, status_name", [
    ("create_paid_order", "已支付"),
    ("create_accepted_order", "已接单"),
    ("create_completed_order", "已完成"),
    ("create_refunded_order", "已退款"),
])
def test_cancel_invalid_status(base_url, db, dish_factory, cart_factory, customer_ctx, merchant_ctx, order_factory,
                                create_fn, status_name):
    """取消失败：从非法状态"""
    user_id, headers = customer_ctx()
    _, merchant_h = merchant_ctx()

    fn = globals()[create_fn]
    order_id = fn(dish_factory, cart_factory, order_factory, base_url, headers, merchant_h)   # ← 统一 6 个

    rows = db.execute_query("SELECT status FROM orders WHERE id = ?", (order_id,))
    assert rows[0]["status"] == status_name

    r = requests.post(f"{base_url}/orders/{order_id}/cancel", headers=headers)
    assert r.status_code == 400


def test_cancel_twice(base_url, db, dish_factory, cart_factory, customer_ctx, merchant_ctx, order_factory):
    """重复取消：第二次 400"""
    user_id, headers = customer_ctx()
    _, merchant_h = merchant_ctx()

    order_id = create_pending_order(dish_factory, cart_factory, order_factory, base_url, headers, merchant_h)

    r1 = requests.post(f"{base_url}/orders/{order_id}/cancel", headers=headers)
    assert r1.status_code == 200

    r2 = requests.post(f"{base_url}/orders/{order_id}/cancel", headers=headers)
    assert r2.status_code == 400


def test_cancel_not_exist(base_url, db, customer_ctx):
    """取消不存在的订单：400"""
    user_id, headers = customer_ctx()

    rows = db.execute_query("SELECT * FROM orders WHERE id = 99999")
    assert len(rows) == 0

    r = requests.post(f"{base_url}/orders/99999/cancel", headers=headers)
    assert r.status_code == 400


# ==================== 接单 ====================

def test_accept_paid_order(base_url, db, dish_factory, cart_factory, customer_ctx, merchant_ctx, order_factory):
    """接已支付的订单：成功"""
    user_id, headers = customer_ctx()
    _, merchant_h = merchant_ctx()

    order_id = create_paid_order(dish_factory, cart_factory, order_factory, base_url, headers, merchant_h)

    r = requests.post(f"{base_url}/orders/{order_id}/accept", headers=merchant_h)   # ← 商户 token
    assert r.status_code == 200, f"接单失败：{r.text}"

    rows = db.execute_query("SELECT status FROM orders WHERE id = ?", (order_id,))
    assert rows[0]["status"] == "已接单"


@pytest.mark.parametrize("create_fn, status_name", [
    ("create_pending_order", "待支付"),
    ("create_accepted_order", "已接单"),
    ("create_completed_order", "已完成"),
    ("create_cancelled_order", "已取消"),
    ("create_refunded_order", "已退款"),
])
def test_accept_invalid_status(base_url, db, dish_factory, cart_factory, customer_ctx, merchant_ctx, order_factory,
                                create_fn, status_name):
    """接单失败：从非法状态"""
    user_id, headers = customer_ctx()
    _, merchant_h = merchant_ctx()

    fn = globals()[create_fn]
    order_id = fn(dish_factory, cart_factory, order_factory, base_url, headers, merchant_h)   # ← 统一 6 个

    rows = db.execute_query("SELECT status FROM orders WHERE id = ?", (order_id,))
    assert rows[0]["status"] == status_name

    r = requests.post(f"{base_url}/orders/{order_id}/accept", headers=merchant_h)
    assert r.status_code == 400


def test_accept_not_exist(base_url, db, merchant_ctx):
    """接单不存在的订单：400"""
    _, merchant_h = merchant_ctx()

    rows = db.execute_query("SELECT * FROM orders WHERE id = 99999")
    assert len(rows) == 0

    r = requests.post(f"{base_url}/orders/99999/accept", headers=merchant_h)
    assert r.status_code == 400


# ==================== 完成 ====================

def test_complete_accepted_order(base_url, db, dish_factory, cart_factory, customer_ctx, merchant_ctx, order_factory):
    """完成已接单的订单：成功"""
    user_id, headers = customer_ctx()
    _, merchant_h = merchant_ctx()

    order_id = create_accepted_order(dish_factory, cart_factory, order_factory, base_url, headers, merchant_h)

    r = requests.post(f"{base_url}/orders/{order_id}/complete", headers=merchant_h)
    assert r.status_code == 200, f"完成失败：{r.text}"

    rows = db.execute_query("SELECT status FROM orders WHERE id = ?", (order_id,))
    assert rows[0]["status"] == "已完成"


@pytest.mark.parametrize("create_fn, status_name", [
    ("create_pending_order", "待支付"),
    ("create_paid_order", "已支付"),
    ("create_completed_order", "已完成"),
    ("create_cancelled_order", "已取消"),
    ("create_refunded_order", "已退款"),
])
def test_complete_invalid_status(base_url, db, dish_factory, cart_factory, customer_ctx, merchant_ctx, order_factory,
                                  create_fn, status_name):
    """完成失败：从非法状态"""
    user_id, headers = customer_ctx()
    _, merchant_h = merchant_ctx()

    fn = globals()[create_fn]
    order_id = fn(dish_factory, cart_factory, order_factory, base_url, headers, merchant_h)   # ← 统一 6 个

    rows = db.execute_query("SELECT status FROM orders WHERE id = ?", (order_id,))
    assert rows[0]["status"] == status_name

    r = requests.post(f"{base_url}/orders/{order_id}/complete", headers=merchant_h)
    assert r.status_code == 400


def test_complete_not_exist(base_url, db, merchant_ctx):
    """完成不存在的订单：400"""
    _, merchant_h = merchant_ctx()

    rows = db.execute_query("SELECT * FROM orders WHERE id = 99999")
    assert len(rows) == 0

    r = requests.post(f"{base_url}/orders/99999/complete", headers=merchant_h)
    assert r.status_code == 400


# ==================== 退款 ====================

def test_refund_paid_order(base_url, db, dish_factory, cart_factory, customer_ctx, merchant_ctx, order_factory):
    """退款已支付的订单：成功"""
    user_id, headers = customer_ctx()
    _, merchant_h = merchant_ctx()

    order_id = create_paid_order(dish_factory, cart_factory, order_factory, base_url, headers, merchant_h)

    payments_before = db.execute_query(
        "SELECT status FROM payments WHERE order_id = ?",
        (order_id,)
    )
    assert len(payments_before) == 1
    assert payments_before[0]["status"] == "支付成功"

    r = requests.post(f"{base_url}/orders/{order_id}/refund", headers=headers)
    assert r.status_code == 200, f"退款失败：{r.text}"

    orders = db.execute_query("SELECT status FROM orders WHERE id = ?", (order_id,))
    assert orders[0]["status"] == "已退款"

    payments_after = db.execute_query(
        "SELECT status FROM payments WHERE order_id = ?",
        (order_id,)
    )
    assert payments_after[0]["status"] == "已退款"


@pytest.mark.parametrize("create_fn, status_name", [
    ("create_pending_order", "待支付"),
    ("create_accepted_order", "已接单"),
    ("create_completed_order", "已完成"),
    ("create_cancelled_order", "已取消"),
    ("create_refunded_order", "已退款"),
])
def test_refund_invalid_status(base_url, db, dish_factory, cart_factory, customer_ctx, merchant_ctx, order_factory,
                                create_fn, status_name):
    """退款失败：从非法状态"""
    user_id, headers = customer_ctx()
    _, merchant_h = merchant_ctx()

    fn = globals()[create_fn]
    order_id = fn(dish_factory, cart_factory, order_factory, base_url, headers, merchant_h)   # ← 统一 6 个

    rows = db.execute_query("SELECT status FROM orders WHERE id = ?", (order_id,))
    assert rows[0]["status"] == status_name

    r = requests.post(f"{base_url}/orders/{order_id}/refund", headers=headers)
    assert r.status_code == 400


def test_refund_not_exist(base_url, db, customer_ctx):
    """退款不存在的订单：400"""
    user_id, headers = customer_ctx()

    rows = db.execute_query("SELECT * FROM orders WHERE id = 99999")
    assert len(rows) == 0

    r = requests.post(f"{base_url}/orders/99999/refund", headers=headers)
    assert r.status_code == 400