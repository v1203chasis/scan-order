"""订单状态流转测试（Part 9）"""
import requests
import pytest


# ==================== 辅助函数 ====================

def create_pending_order(dish_factory, cart_factory, order_factory):
    """创建一个待支付的订单，返回 order_id"""
    dish_id = dish_factory(name="测试菜", price=20.0)
    cart_factory(dish_id=dish_id, quantity=1)
    return order_factory()


def create_paid_order(dish_factory, cart_factory, order_factory, base_url):
    """创建一个已支付的订单，返回 order_id"""
    order_id = create_pending_order(dish_factory, cart_factory, order_factory)
    r = requests.post(f"{base_url}/orders/{order_id}/pay")
    assert r.status_code == 200, f"辅助：支付失败 {r.text}"
    return order_id


def create_accepted_order(dish_factory, cart_factory, order_factory, base_url):
    """创建一个已接单的订单，返回 order_id"""
    order_id = create_paid_order(dish_factory, cart_factory, order_factory, base_url)
    r = requests.post(f"{base_url}/orders/{order_id}/accept")
    assert r.status_code == 200, f"辅助：接单失败 {r.text}"
    return order_id


def create_completed_order(dish_factory, cart_factory, order_factory, base_url):
    """创建一个已完成的订单，返回 order_id"""
    order_id = create_accepted_order(dish_factory, cart_factory, order_factory, base_url)
    r = requests.post(f"{base_url}/orders/{order_id}/complete")
    assert r.status_code == 200, f"辅助：完成失败 {r.text}"
    return order_id


def create_cancelled_order(dish_factory, cart_factory, order_factory, base_url):
    """创建一个已取消的订单，返回 order_id"""
    order_id = create_pending_order(dish_factory, cart_factory, order_factory)
    r = requests.post(f"{base_url}/orders/{order_id}/cancel")
    assert r.status_code == 200, f"辅助：取消失败 {r.text}"
    return order_id


def create_refunded_order(dish_factory, cart_factory, order_factory, base_url):
    """创建一个已退款的订单，返回 order_id"""
    order_id = create_paid_order(dish_factory, cart_factory, order_factory, base_url)
    r = requests.post(f"{base_url}/orders/{order_id}/refund")
    assert r.status_code == 200, f"辅助：退款失败 {r.text}"
    return order_id


# ==================== 取消订单 ====================

def test_cancel_pending_order(base_url, db, dish_factory, cart_factory, order_factory):
    """取消待支付的订单：成功"""
    order_id = create_pending_order(dish_factory, cart_factory, order_factory)

    # 验证前置条件
    rows = db.execute_query("SELECT status FROM orders WHERE id = ?", (order_id,))
    assert rows[0]["status"] == "待支付"

    # 取消
    r = requests.post(f"{base_url}/orders/{order_id}/cancel")
    assert r.status_code == 200, f"取消失败：{r.text}"

    # 验证状态
    rows = db.execute_query("SELECT status FROM orders WHERE id = ?", (order_id,))
    assert rows[0]["status"] == "已取消"


@pytest.mark.parametrize("create_fn, status_name", [
    ("create_paid_order", "已支付"),
    ("create_accepted_order", "已接单"),
    ("create_completed_order", "已完成"),
    ("create_refunded_order", "已退款"),
])
#create_fn只是字符串，而我们要的是这个函数名的函数功能，所以需要fn=globals（）[create_fn]来去全局找叫这个名字的函数，将它的功能赋能给fn
#然后order_id = fn(...)相当于 order_id = create_paid_oredr(...)

def test_cancel_invalid_status(base_url, db, dish_factory, cart_factory, order_factory,
                                create_fn, status_name):
    """取消失败：从非法状态"""
    # 动态调辅助函数
    fn = globals()[create_fn]
    order_id = fn(dish_factory, cart_factory, order_factory, base_url)

    # 验证前置条件
    rows = db.execute_query("SELECT status FROM orders WHERE id = ?", (order_id,))
    assert rows[0]["status"] == status_name

    r = requests.post(f"{base_url}/orders/{order_id}/cancel")
    assert r.status_code == 400


def test_cancel_twice(base_url, db, dish_factory, cart_factory, order_factory):
    """重复取消：第二次 400"""
    order_id = create_pending_order(dish_factory, cart_factory, order_factory)

    r1 = requests.post(f"{base_url}/orders/{order_id}/cancel")
    assert r1.status_code == 200

    r2 = requests.post(f"{base_url}/orders/{order_id}/cancel")
    assert r2.status_code == 400


def test_cancel_not_exist(base_url, db):
    """取消不存在的订单：400"""
    rows = db.execute_query("SELECT * FROM orders WHERE id = 99999")
    assert len(rows) == 0

    r = requests.post(f"{base_url}/orders/99999/cancel")
    assert r.status_code == 400


# ==================== 接单 ====================

def test_accept_paid_order(base_url, db, dish_factory, cart_factory, order_factory):
    """接已支付的订单：成功"""
    order_id = create_paid_order(dish_factory, cart_factory, order_factory, base_url)

    r = requests.post(f"{base_url}/orders/{order_id}/accept")
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
def test_accept_invalid_status(base_url, db, dish_factory, cart_factory, order_factory,
                                create_fn, status_name):
    """接单失败：从非法状态"""
    fn = globals()[create_fn]
    if create_fn == "create_pending_order":
        order_id = fn(dish_factory, cart_factory, order_factory)
    else:
        order_id = fn(dish_factory, cart_factory, order_factory, base_url)

    rows = db.execute_query("SELECT status FROM orders WHERE id = ?", (order_id,))
    assert rows[0]["status"] == status_name

    r = requests.post(f"{base_url}/orders/{order_id}/accept")
    assert r.status_code == 400


def test_accept_not_exist(base_url, db):
    """接单不存在的订单：400"""
    rows = db.execute_query("SELECT * FROM orders WHERE id = 99999")
    assert len(rows) == 0

    r = requests.post(f"{base_url}/orders/99999/accept")
    assert r.status_code == 400


# ==================== 完成 ====================

def test_complete_accepted_order(base_url, db, dish_factory, cart_factory, order_factory):
    """完成已接单的订单：成功"""
    order_id = create_accepted_order(dish_factory, cart_factory, order_factory, base_url)

    r = requests.post(f"{base_url}/orders/{order_id}/complete")
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
def test_complete_invalid_status(base_url, db, dish_factory, cart_factory, order_factory,
                                  create_fn, status_name):
    """完成失败：从非法状态"""
    fn = globals()[create_fn]
    if create_fn == "create_pending_order":
        order_id = fn(dish_factory, cart_factory, order_factory)
    else:
        order_id = fn(dish_factory, cart_factory, order_factory, base_url)

    rows = db.execute_query("SELECT status FROM orders WHERE id = ?", (order_id,))
    assert rows[0]["status"] == status_name

    r = requests.post(f"{base_url}/orders/{order_id}/complete")
    assert r.status_code == 400


def test_complete_not_exist(base_url, db):
    """完成不存在的订单：400"""
    rows = db.execute_query("SELECT * FROM orders WHERE id = 99999")
    assert len(rows) == 0

    r = requests.post(f"{base_url}/orders/99999/complete")
    assert r.status_code == 400


# ==================== 退款 ====================

def test_refund_paid_order(base_url, db, dish_factory, cart_factory, order_factory):
    """退款已支付的订单：成功"""
    order_id = create_paid_order(dish_factory, cart_factory, order_factory, base_url)

    # 前置条件
    payments_before = db.execute_query(
        "SELECT status FROM payments WHERE order_id = ?",
        (order_id,)
    )
    assert len(payments_before) == 1
    assert payments_before[0]["status"] == "支付成功"

    # 退款
    r = requests.post(f"{base_url}/orders/{order_id}/refund")
    assert r.status_code == 200, f"退款失败：{r.text}"

    # 验证 orders 状态
    orders = db.execute_query("SELECT status FROM orders WHERE id = ?", (order_id,))
    assert orders[0]["status"] == "已退款"

    # 验证 payments 状态
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
def test_refund_invalid_status(base_url, db, dish_factory, cart_factory, order_factory,
                                create_fn, status_name):
    """退款失败：从非法状态"""
    fn = globals()[create_fn]
    if create_fn == "create_pending_order":
        order_id = fn(dish_factory, cart_factory, order_factory)
    else:
        order_id = fn(dish_factory, cart_factory, order_factory, base_url)

    rows = db.execute_query("SELECT status FROM orders WHERE id = ?", (order_id,))
    assert rows[0]["status"] == status_name

    r = requests.post(f"{base_url}/orders/{order_id}/refund")
    assert r.status_code == 400


def test_refund_not_exist(base_url, db):
    """退款不存在的订单：400"""
    rows = db.execute_query("SELECT * FROM orders WHERE id = 99999")
    assert len(rows) == 0

    r = requests.post(f"{base_url}/orders/99999/refund")
    assert r.status_code == 400