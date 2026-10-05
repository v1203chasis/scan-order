from app.db_helper import execute_update, execute_query


def create_dish(name: str, price: float) -> int:
    sql = "INSERT INTO dishes (name, price) VALUES (?, ?)"
    return execute_update(sql, (name, price))


# ==================== 公共查询常量 ====================

_BASE_QUERY = "SELECT id, name, price, status FROM dishes WHERE id = ? AND is_deleted = 0"
_BASE_LIST_QUERY = "SELECT id, name, price, status FROM dishes WHERE is_deleted = 0"


# ==================== 商户视角（能看到下架的菜） ====================

def get_dish_by_id(dish_id: int):
    """商户视角：查单个菜（能看到下架的，看不到软删除的）"""
    rows = execute_query(_BASE_QUERY, (dish_id,))
    return rows[0] if rows else None


def get_dish_by_name(name: str):
    """商户视角：按菜名查（用于菜名唯一性校验）"""
    sql = "SELECT id, name, price, status FROM dishes WHERE name = ? AND is_deleted = 0"
    rows = execute_query(sql, (name,))
    return rows[0] if rows else None


def get_all_dishes():
    """商户视角：查所有菜（包括下架的，不包括软删除的）"""
    rows = execute_query(_BASE_LIST_QUERY, ())
    return rows if rows else []


# ==================== 顾客视角（只能看到上架的菜） ====================

def get_available_dish_by_id(dish_id: int):
    """顾客视角：查单个上架的菜"""
    sql = _BASE_QUERY + " AND status = 1"
    rows = execute_query(sql, (dish_id,))
    return rows[0] if rows else None


def get_available_dishes():
    """顾客视角：查所有上架的菜（菜单列表）"""
    sql = _BASE_LIST_QUERY + " AND status = 1"
    rows = execute_query(sql, ())
    return rows if rows else []

###软删除函数
def soft_delete_dish(dish_id: int):
    sql = "UPDATE dishes SET is_deleted = 1 WHERE id = ? AND is_deleted = 0"
    return execute_update(sql, (dish_id,)) > 0



def update_dish_by_id(dish_id: int, price: float):
    # 1. 先查，判断是否存在（注意：这里必须过滤掉软删除的菜）
    # 如果菜已经软删除了，你还能改它的价格吗？显然不能。
    rows = execute_query("SELECT * FROM dishes WHERE id = ? AND is_deleted = 0", (dish_id,))
    if not rows:
        return None  # 返回 None，上层路由收到 None 后返回 404 JSON

    # 2. 更新价格 (同样加上 is_deleted = 0 双重保险，防止并发时被删)
    execute_update("UPDATE dishes SET price = ? WHERE id = ? AND is_deleted = 0", (price, dish_id))

    # 3. 返回更新后的记录
    return get_dish_by_id(dish_id)
#优化点：如何在查询到菜品不存在的情况下可以将其添加成新菜品
#如果我在这里写
'''
if not rows:
    retrun{
        "code":404
        "msg":"菜品不存在！"
    }
    会怎么样
'''
def update_dish_status(dish_id: int, status: int):
    # 只能操作未被软删除的菜
    sql = "UPDATE dishes SET status = ? WHERE id = ? AND is_deleted = 0"
    result = execute_update(sql, (status, dish_id))
    return result > 0  # 返回受影响行数是否大于0，表示操作成功

def soft_delete_dish(dish_id: int):
    # 先检查是否存在且未被软删除
    sql_check = "SELECT * FROM dishes WHERE id = ? AND is_deleted = 0"
    rows = execute_query(sql_check, (dish_id,))
    if not rows:
        return False  # 不存在或已经软删过了
    
    # 执行软删除
    sql_delete = "UPDATE dishes SET is_deleted = 1 WHERE id = ?"
    execute_update(sql_delete, (dish_id,))
    return True

def get_dish_by_id_include_deleted(dish_id: int):
    """仅用于测试/历史订单：包含已软删除的菜品"""
    sql = "SELECT id, name, price, status, is_deleted FROM dishes WHERE id = ?"
    rows = execute_query(sql, (dish_id,))
    return rows[0] if rows else None


#下架商品
def hard_delete_dish(dish_id: int):
    """
    ⚠️ 仅用于测试环境清理数据。生产环境严禁调用。
    TODO: Part 7 完成后，这里必须加订单关联检查。
    """
    # if has_orders(dish_id):
    #     raise Exception("该菜品已有订单记录，不能物理删除！")
    sql = "DELETE FROM dishes WHERE id = ?"
    return execute_update(sql, (dish_id,)) > 0





































import os
import pytest
from app import db_helper


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    # 测试前，删掉旧库，建一个干净的
    test_db = "test_scan_order.db"
    if os.path.exists(test_db):
        os.remove(test_db)
    os.environ["DB_PATH"] = test_db
    db_helper.init_db()
    yield
    # 测试结束后可删可留
    # os.remove(test_db)