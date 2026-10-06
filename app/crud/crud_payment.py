"""支付 CRUD"""
import uuid
from app.db_helper import execute_query, execute_update, get_conn
from app.crud.crud_order import get_order_by_id


def pay_order(order_id: int, method: str = "模拟支付"):
    """
    支付订单（事务：插入支付记录 + 更新订单状态）
    返回：(payment_id, None) 或 (None, error_msg)
    """
    # 1. 查订单
    order = get_order_by_id(order_id)
    if not order:
        return None, "订单不存在"

    # 2. 检查订单状态
    if order["status"] != "待支付":
        return None, f"订单状态为 {order['status']}，无法支付"

    # 3. 事务
    with get_conn() as conn:
        try:
            conn.execute("BEGIN")

            # 3.1 插入支付记录
            transaction_id = f"TXN_{uuid.uuid4().hex[:12]}"
            cursor = conn.execute(
                """
                INSERT INTO payments (order_id, amount, method, status, transaction_id)
                VALUES (?, ?, ?, ?, ?)
                """,
                (order_id, order["total"], method, "支付成功", transaction_id)
            )
            payment_id = cursor.lastrowid

            # 3.2 更新订单状态（乐观锁）
            result = conn.execute(
                "UPDATE orders SET status = '已支付' WHERE id = ? AND status = '待支付'",
                (order_id,)
            ).rowcount

            if result == 0:
                conn.rollback()
                return None, "支付失败，订单状态已变化"

            conn.commit()
            return payment_id, None
        except Exception as e:
            conn.rollback()
            raise e


def get_payment_by_id(payment_id: int):#一次支付一条记录
    """查看支付记录详情"""
    rows = execute_query(
        "SELECT id, order_id, amount, method, status, transaction_id, created_at FROM payments WHERE id = ?",
        (payment_id,)
    )
    return rows[0] if rows else None


def get_payments_by_order(order_id: int):#一个订单可能有多支付记录（支付失败重试，支付成功。。。）这就是"支付日志"——记录用户的所有支付尝试。
    """查看某个订单的所有支付记录"""
    rows = execute_query(
        "SELECT id, order_id, amount, method, status, transaction_id, created_at FROM payments WHERE order_id = ? ORDER BY id DESC",
        (order_id,)
    )
    return rows if rows else []