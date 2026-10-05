"""顾客视角测试（Part 5）"""
import requests


# ==================== 单个菜品详情 ====================

def test_customer_can_see_on_shelf(base_url, dish_factory):
    """上架的菜，顾客能查到"""
    dish_id = dish_factory(name="测试菜", price=10.0)
    r = requests.get(f"{base_url}/menu/dish/{dish_id}")
    assert r.status_code == 200
    assert r.json()["data"]["status"] == 1
    assert r.json()["data"]["name"] == "测试菜"


def test_customer_cannot_see_off_shelf(base_url, dish_factory):
    """下架的菜，顾客查不到（404）"""
    dish_id = dish_factory(name="测试菜", price=10.0)
    requests.patch(f"{base_url}/dish/{dish_id}/status", json={"status": 0})
    r = requests.get(f"{base_url}/menu/dish/{dish_id}")
    assert r.status_code == 404


def test_customer_cannot_see_soft_deleted(base_url, dish_factory):
    """软删除的菜，顾客查不到（404）"""
    dish_id = dish_factory(name="测试菜", price=10.0)
    requests.delete(f"{base_url}/dish/{dish_id}")
    r = requests.get(f"{base_url}/menu/dish/{dish_id}")
    assert r.status_code == 404


def test_customer_cannot_see_not_exist(base_url):
    """不存在的菜，顾客查不到（404）"""
    r = requests.get(f"{base_url}/menu/dish/9999")
    assert r.status_code == 404


# ==================== 菜单列表 ====================

def test_menu_only_shows_available(base_url, dish_factory):
    """顾客菜单只显示上架的菜"""
    dish_1 = dish_factory(name="上架菜", price=10.0)
    dish_2 = dish_factory(name="下架菜", price=20.0)
    dish_3 = dish_factory(name="删除菜", price=30.0)

    requests.patch(f"{base_url}/dish/{dish_2}/status", json={"status": 0})
    requests.delete(f"{base_url}/dish/{dish_3}")

    r = requests.get(f"{base_url}/menu")
    assert r.status_code == 200
    ids = [d["id"] for d in r.json()["data"]]

    assert dish_1 in ids
    assert dish_2 not in ids
    assert dish_3 not in ids


def test_menu_returns_empty_list_when_no_dishes(base_url):
    """菜单为空时，返回空列表"""
    r = requests.get(f"{base_url}/menu")
    assert r.status_code == 200
    assert isinstance(r.json()["data"], list)


def test_menu_dish_invalid_id(base_url):
    """dish_id 非法（0、-1、abc）都返回 422"""
    for invalid_id in ["0", "-1", "abc"]:
        r = requests.get(f"{base_url}/menu/dish/{invalid_id}")
        assert r.status_code == 422, f"dish_id={invalid_id} 应该返回 422"