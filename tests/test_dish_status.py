"""上下架测试"""
import requests
import pytest


# ==================== 下架 ====================

def test_off_shelf_success(base_url, db, dish_factory):
    """下架成功：状态变 0，商家能查到"""
    dish_id = dish_factory(name="下架菜", price=12)

    rows = db.execute_query("SELECT status FROM dishes WHERE id = ?", (dish_id,))
    assert rows[0]["status"] == 1

    r = requests.patch(f"{base_url}/dish/{dish_id}/status", json={"status": 0})
    assert r.status_code == 200, "下架失败！"
    assert r.json()["data"]["status"] == 0

    r_get = requests.get(f"{base_url}/dish/{dish_id}")
    assert r_get.status_code == 200
    assert r_get.json()["data"]["status"] == 0

    rows = db.execute_query("SELECT status FROM dishes WHERE id = ?", (dish_id,))
    assert rows[0]["status"] == 0


def test_off_shelf_twice(base_url, dish_factory):
    """重复下架：返回 400"""
    dish_id = dish_factory(name="测试下架菜", price=10.0)

    r1 = requests.patch(f"{base_url}/dish/{dish_id}/status", json={"status": 0})
    assert r1.status_code == 200

    r2 = requests.patch(f"{base_url}/dish/{dish_id}/status", json={"status": 0})
    assert r2.status_code == 400


def test_off_shelf_not_exist(base_url):
    """下架不存在的菜：404"""
    r = requests.patch(f"{base_url}/dish/9999/status", json={"status": 0})
    assert r.status_code == 404


# ==================== 上架 ====================

def test_on_shelf_success(base_url, db, dish_factory):
    """上架成功：状态变 1，商家能查到"""
    dish_id = dish_factory(name="上架菜", price=12.0)

    r_down = requests.patch(f"{base_url}/dish/{dish_id}/status", json={"status": 0})
    assert r_down.status_code == 200

    rows = db.execute_query("SELECT status FROM dishes WHERE id = ?", (dish_id,))
    assert rows[0]["status"] == 0

    r = requests.patch(f"{base_url}/dish/{dish_id}/status", json={"status": 1})
    assert r.status_code == 200, f"上架失败：{r.text}"
    assert r.json()["data"]["status"] == 1

    r_get = requests.get(f"{base_url}/dish/{dish_id}")
    assert r_get.status_code == 200
    assert r_get.json()["data"]["status"] == 1

    rows = db.execute_query("SELECT status FROM dishes WHERE id = ?", (dish_id,))
    assert rows[0]["status"] == 1


def test_on_shelf_twice(base_url, db, dish_factory):
    """重复上架：返回 400"""
    dish_id = dish_factory(name="测试上架菜", price=10.0)

    r_down = requests.patch(f"{base_url}/dish/{dish_id}/status", json={"status": 0})
    assert r_down.status_code == 200

    r1 = requests.patch(f"{base_url}/dish/{dish_id}/status", json={"status": 1})
    assert r1.status_code == 200

    r2 = requests.patch(f"{base_url}/dish/{dish_id}/status", json={"status": 1})
    assert r2.status_code == 400

    rows = db.execute_query(
        "SELECT status FROM dishes WHERE id = ? AND is_deleted = 0",
        (dish_id,)
    )
    assert rows[0]["status"] == 1


def test_on_shelf_not_exist(base_url):
    """上架不存在的菜：404"""
    r = requests.patch(f"{base_url}/dish/9999/status", json={"status": 1})
    assert r.status_code == 404


# ==================== 参数校验 ====================

def test_update_status_invalid(base_url, dish_factory):
    """非法 status 返回 422"""
    dish_id = dish_factory(name="测试菜", price=10.0)
    r = requests.patch(f"{base_url}/dish/{dish_id}/status", json={"status": 2})
    assert r.status_code == 422