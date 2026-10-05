"""软删除测试"""
import requests


# ==================== 软删除本身 ====================

def test_soft_delete_dish_success(base_url, dish_factory, db):
    """软删除成功：is_deleted 变成 1，且查询查不到"""
    dish_id = dish_factory(name="软删除的菜", price=12.0)

    rows = db.execute_query(
        "SELECT name, price FROM dishes WHERE id = ? AND is_deleted = 0",
        (dish_id,)
    )
    assert len(rows) == 1, "数据库里应该有菜品"

    res = requests.delete(f"{base_url}/dish/{dish_id}")
    assert res.status_code == 200, f"软删除失败：{res.text}"
    assert res.json()["msg"] == "菜品已移入回收站"

    rows = db.execute_query("SELECT is_deleted FROM dishes WHERE id = ?", (dish_id,))
    assert len(rows) == 1, "软删除后数据应该还在数据库里"
    assert rows[0]["is_deleted"] == 1

    response = requests.get(f"{base_url}/dish/{dish_id}")
    assert response.status_code == 404


def test_soft_delete_twice(base_url, dish_factory):
    """重复软删除：第二次失败（404）"""
    dish_id = dish_factory(name="软删除菜", price=10.0)

    r1 = requests.delete(f"{base_url}/dish/{dish_id}")
    assert r1.status_code == 200

    r2 = requests.delete(f"{base_url}/dish/{dish_id}")
    assert r2.status_code == 404


def test_soft_delete_not_exist(base_url):
    """软删除不存在的菜：404"""
    r = requests.delete(f"{base_url}/dish/9999")
    assert r.status_code == 404


def test_soft_delete_data_still_in_db(base_url, dish_factory, db):
    """软删除后，数据还在数据库里（不是物理删除）"""
    dish_id = dish_factory(name="软删除菜", price=10.0)
    requests.delete(f"{base_url}/dish/{dish_id}")

    rows = db.execute_query("SELECT * FROM dishes WHERE id = ?", (dish_id,))
    assert len(rows) == 1, "软删除后数据应该还在数据库里"
    assert rows[0]["is_deleted"] == 1
    assert rows[0]["name"] == "软删除菜"
    assert rows[0]["price"] == 10.0


# ==================== 软删除对查询的影响 ====================

def test_query_after_soft_delete(base_url, dish_factory):
    """软删除后，商家查询查不到（404）"""
    dish_id = dish_factory(name="软删除菜", price=10.0)
    requests.delete(f"{base_url}/dish/{dish_id}")

    r = requests.get(f"{base_url}/dish/{dish_id}")
    assert r.status_code == 404


# ==================== 软删除对修改的影响 ====================

def test_update_price_after_soft_delete(base_url, dish_factory):
    """软删除后，修改价格失败（404）"""
    dish_id = dish_factory(name="软删除菜", price=10.0)
    requests.delete(f"{base_url}/dish/{dish_id}")

    r = requests.put(f"{base_url}/dish/{dish_id}", json={"price": 52.0})
    assert r.status_code == 404


# ==================== 软删除对上下架的影响 ====================

def test_update_status_after_soft_delete(base_url, dish_factory):
    """软删除后，上下架失败（404）"""
    dish_id = dish_factory(name="软删除菜", price=10.0)
    requests.delete(f"{base_url}/dish/{dish_id}")

    r1 = requests.patch(f"{base_url}/dish/{dish_id}/status", json={"status": 0})
    assert r1.status_code == 404

    r2 = requests.patch(f"{base_url}/dish/{dish_id}/status", json={"status": 1})
    assert r2.status_code == 404


# ==================== 软删除对添加的影响 ====================

def test_add_same_name_after_soft_delete(base_url, dish_factory, db):
    """软删除后，可以重新添加同名菜品"""
    dish_id_1 = dish_factory(name="宫保鸡肉", price=10.0)
    requests.delete(f"{base_url}/dish/{dish_id_1}")

    r = requests.post(f"{base_url}/dish", json={"name": "宫保鸡肉", "price": 15.0})
    assert r.status_code == 200
    dish_id_2 = r.json()["data"]["id"]

    assert dish_id_2 != dish_id_1, "新菜应该是新记录，不是原记录"

    db.execute_update("DELETE FROM dishes WHERE id = ?", (dish_id_2,))


def test_add_duplicate_name_blocked(base_url, dish_factory):
    """未软删除的同名菜品，不能重复添加（400）"""
    dish_factory(name="宫保鸡肉", price=10.0)

    r = requests.post(f"{base_url}/dish", json={"name": "宫保鸡肉", "price": 15.0})
    assert r.status_code == 400