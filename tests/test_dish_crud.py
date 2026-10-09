"""基础 CRUD 测试：添加、查询、修改"""
import requests
import pytest
from tests.utils import load_yaml


# ==================== 添加菜品 ====================

@pytest.mark.parametrize("name, price", [
    ("宫保鸡丁", 38.0),
    ("麻婆豆腐", 28.0),
    ("水煮牛肉", 58.0),
])
def test_create_dish_success(base_url, db, name, price):
    """添加菜品成功"""
    r = requests.post(f"{base_url}/dish", json={"name": name, "price": price})
    assert r.status_code == 200
    result = r.json()
    assert result["data"]["name"] == name
    assert result["data"]["price"] == price

    dish_id = result["data"]["id"]
    rows = db.execute_query("SELECT name, price FROM dishes WHERE id = ?", (dish_id,))
    assert len(rows) == 1
    assert rows[0]["name"] == name
    assert rows[0]["price"] == price


@pytest.mark.parametrize("payload", [
    pytest.param({"name": "免费菜", "price": 0}, id="price_zero"),
    pytest.param({"name": "倒贴菜", "price": -1}, id="price_negative"),
    pytest.param({"name": "", "price": 10}, id="name_empty"),
    pytest.param({"price": 10}, id="name_missing"),
    pytest.param({"name": "类型错", "price": "abc"}, id="price_wrong_type"),
])
def test_create_dish_invalid_payload(base_url, payload):
    """添加菜品：非法 payload 返回 422"""
    res = requests.post(f"{base_url}/dish", json=payload)
    assert res.status_code == 422


def test_create_dish_duplicate(base_url, dish_factory):
    """菜名重复返回 400"""
    dish_factory(name="神秘功夫", price=38.0)
    r = requests.post(f"{base_url}/dish", json={"name": "神秘功夫", "price": 28.0})
    assert r.status_code == 400
    assert r.json()["detail"] == "菜名已存在"


# ==================== 查询单个菜品 ====================

@pytest.mark.parametrize("name, price", [("番茄炒蛋", 6.0)])
def test_get_dish_by_id(base_url, db, dish_factory, name, price):
    """商户按 ID 查询成功"""
    dish_id = dish_factory(name=name, price=price)

    rows = db.execute_query("SELECT name, price FROM dishes WHERE id = ?", (dish_id,))
    assert rows[0]["name"] == name
    assert rows[0]["price"] == price

    res = requests.get(f"{base_url}/dish/{dish_id}")
    assert res.status_code == 200, "查询失败！"
    assert res.json()["data"]["name"] == name
    assert res.json()["data"]["price"] == price


def test_get_dish_by_id_not_exist(base_url, db):
    """商户按 ID 查询不存在：404"""
    rows = db.execute_query("SELECT name, price FROM dishes WHERE id = 9999")
    assert len(rows) == 0, "数据库里不应该有这个 id"

    res = requests.get(f"{base_url}/dish/9999")
    assert res.status_code == 404


@pytest.mark.parametrize(
    "case",
    load_yaml("test_data/invalid_dish_id_cases.yaml"),
    ids=lambda c: c["case_name"]
)
def test_get_dish_by_id_invalid(base_url, case):
    """商户按 ID 查询：非法 ID 返回 422"""
    res = requests.get(f"{base_url}/dish/{case['invalid_id']}")
    assert res.status_code == case["expected_status"]


# ==================== 按名字查询 ====================

@pytest.mark.parametrize("name, price", [("青椒炒蛋", 6.0)])
def test_get_dish_by_name(base_url, db, dish_factory, name, price):
    """商户按名字查询成功"""
    dish_id = dish_factory(name=name, price=price)

    rows = db.execute_query("SELECT name, price FROM dishes WHERE id = ?", (dish_id,))
    assert rows[0]["name"] == name
    assert rows[0]["price"] == price

    res = requests.get(f"{base_url}/dish/name/{name}")
    assert res.status_code == 200
    assert res.json()["data"]["name"] == name
    assert res.json()["data"]["price"] == price


def test_get_dish_by_name_not_exists(base_url, db):
    """商户按名字查询不存在：404"""
    rows = db.execute_query("SELECT id FROM dishes WHERE name = ?", ("不存在的菜品",))
    assert len(rows) == 0

    res = requests.get(f"{base_url}/dish/name/不存在的菜品")
    assert res.status_code == 404
    assert "不存在" in res.json()["detail"]


@pytest.mark.parametrize(
    "case",
    load_yaml("test_data/invalid_dish_name_cases.yaml"),
    ids=lambda c: c["case_name"]
)
def test_get_dish_by_name_invalid(base_url, case):
    """商户按名字查询：非法 name 返回 422"""
    res = requests.get(f"{base_url}/dish/name/{case['invalid_name']}")
    assert res.status_code == case["expected_status"], \
        f"[{case['case_name']}] 期望 {case['expected_status']}，实际 {res.status_code}"


# ==================== 商户查询全部 ====================

def test_get_all_dishes(base_url, dish_factory):
    """商户查所有菜（含下架，不含软删除）"""
    dish_1 = dish_factory(name="上架菜", price=10.0)
    dish_2 = dish_factory(name="下架菜", price=20.0)
    dish_3 = dish_factory(name="删除菜", price=30.0)

    requests.patch(f"{base_url}/dish/{dish_2}/status", json={"status": 0})
    requests.delete(f"{base_url}/dish/{dish_3}")

    r = requests.get(f"{base_url}/dishes")
    assert r.status_code == 200, f"商户查询所有菜失败：{r.text}"
    ids = [d["id"] for d in r.json()["data"]]

    assert dish_1 in ids, "上架的菜应该在列表里"
    assert dish_2 in ids, "下架的菜也应该在列表里（商户视角）"
    assert dish_3 not in ids, "软删除的菜不应该在列表里"


def test_get_all_dishes_empty(base_url):
    """商户查所有菜：空列表返回 []"""
    r = requests.get(f"{base_url}/dishes")
    assert r.status_code == 200
    assert isinstance(r.json()["data"], list), "data 必须是 list"


# ==================== 修改价格 ====================

def test_update_dish_price_success(base_url, db, dish_factory):
    """修改价格成功"""
    dish_id = dish_factory(name="玫瑰雨露", price=13.14)

    rows = db.execute_query("SELECT name, price FROM dishes WHERE id = ?", (dish_id,))
    assert len(rows) == 1

    res = requests.put(f"{base_url}/dish/{dish_id}", json={"price": 52.0})
    assert res.status_code == 200, "修改失败！"
    assert res.json()["msg"] == "修改菜品成功"
    assert res.json()["data"]["name"] == "玫瑰雨露"
    assert res.json()["data"]["price"] == 52.0

    result = db.execute_query("SELECT name, price FROM dishes WHERE id = ?", (dish_id,))
    assert result[0]["name"] == "玫瑰雨露"
    assert result[0]["price"] == 52.0


def test_update_dish_by_id_not_exist(base_url, db):
    """修改不存在的菜：404"""
    dish = db.execute_query("SELECT * FROM dishes WHERE id = 99999")
    assert len(dish) == 0

    res = requests.put(f"{base_url}/dish/99999", json={"price": 10.0})
    assert res.status_code == 404
    assert res.json()["detail"] == "菜品不存在"


@pytest.mark.parametrize(
    "case",
    load_yaml("test_data/invalid_update_dish.yaml"),
    ids=lambda c: c["case_name"]
)
def test_update_dish_by_id_wrong_input(base_url, db, dish_factory, case):
    """修改价格：非法输入返回 422，且不改变数据库"""
    dish_id = dish_factory(name="土豆炒马铃薯", price=5.2)
    rows = db.execute_query("SELECT * FROM dishes WHERE id = ?", (dish_id,))
    assert len(rows) == 1

    res = requests.put(f"{base_url}/dish/{dish_id}", json={"price": case["after_price"]})
    assert res.status_code == 422

    result = db.execute_query("SELECT price FROM dishes WHERE id = ?", (dish_id,))
    assert result[0]["price"] == 5.2, "非法修改不应改变数据库"