"""订单状态流转 CRUD"""
from app.db_helper import execute_update, get_conn
from app.crud.crud_order import get_order_by_id, get_order_by_id_admin


def cancel_order(user_id: int, order_id: int):
    """
    取消订单（待支付 → 已取消）
    顾客操作：只能取消自己的订单
    返回：(True, None) 或 (None, error_msg)
    """
    # 用 user_id 过滤（顾客只能查自己的）
    order = get_order_by_id(order_id, user_id)
    if not order:
        return None, "订单不存在"

    if order["status"] != "待支付":
        return None, f"订单状态为 {order['status']}，无法取消"

    result = execute_update(
        "UPDATE orders SET status = '已取消' WHERE id = ? AND status = '待支付' AND user_id = ?",
        (order_id, user_id)
    )
    if result == 0:
        return None, "取消失败，请重试"

    return True, None


def accept_order(user_id: int, order_id: int):
    """
    商户接单（已支付 → 已接单）
    商户操作：订单属于顾客，不能用 user_id 过滤
    返回：(True, None) 或 (None, error_msg)
    """
    # 不过滤 user_id（商户可以接任何顾客的订单）
    order = get_order_by_id_admin(order_id)
    if not order:
        return None, "订单不存在"

    if order["status"] != "已支付":
        return None, f"订单状态为 {order['status']}，无法接单"

    result = execute_update(
        "UPDATE orders SET status = '已接单' WHERE id = ? AND status = '已支付'",
        (order_id,)
    )
    if result == 0:
        return None, "接单失败，请重试"

    return True, None


def complete_order(user_id: int, order_id: int):
    """
    完成订单（已接单 → 已完成）
    商户操作：订单属于顾客，不能用 user_id 过滤
    返回：(True, None) 或 (None, error_msg)
    """
    # 不过滤 user_id
    order = get_order_by_id_admin(order_id)
    if not order:
        return None, "订单不存在"

    if order["status"] != "已接单":
        return None, f"订单状态为 {order['status']}，无法完成"

    result = execute_update(
        "UPDATE orders SET status = '已完成' WHERE id = ? AND status = '已接单'",
        (order_id,)
    )
    if result == 0:
        return None, "完成失败，请重试"

    return True, None


def refund_order(user_id: int, order_id: int):
    """
    退款（已支付 → 已退款，涉及 orders + payments 两张表）
    顾客操作：只能退款自己的订单
    返回：(True, None) 或 (None, error_msg)
    """
    # 用 user_id 过滤
    order = get_order_by_id(order_id, user_id)
    if not order:
        return None, "订单不存在"

    if order["status"] != "已支付":
        return None, f"订单状态为 {order['status']}，无法退款"

    with get_conn() as conn:
        try:
            conn.execute("BEGIN")

            # 1. 更新支付状态
            result_pay = conn.execute(
                "UPDATE payments SET status = '已退款' WHERE order_id = ? AND status = '支付成功'",
                (order_id,)
            ).rowcount

            if result_pay == 0:
                conn.rollback()
                return None, "没有找到支付记录，无法退款"

            # 2. 更新订单状态
            result_order = conn.execute(
                "UPDATE orders SET status = '已退款' WHERE id = ? AND status = '已支付'",
                (order_id,)
            ).rowcount

            if result_order == 0:
                conn.rollback()
                return None, "订单状态已变化，无法退款"

            conn.commit()
            return True, None
        except Exception as e:
            conn.rollback()
            raise e