"""购物车测试（Part 6）"""
import requests
import pytest


# ==================== 加入购物车 ====================

@pytest.mark.parametrize("name, price, quantity", [("加入购物车的菜", 6.0, 2)])
def test_add_to_cart_success(base_url, db, dish_factory, cart_factory, customer_ctx, name, price, quantity):
    """正确加入购物车"""
    _, headers = customer_ctx()   # ← 用 _ 忽略 user_id
    dish_id = dish_factory(name=name, price=price)
    cart_id = cart_factory(dish_id=dish_id, quantity=quantity, headers=headers)
    assert cart_id is not None

    res = requests.get(f"{base_url}/cart", headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    item = next((d for d in data if d["dish_id"] == dish_id), None)
    assert item is not None
    assert item["quantity"] == quantity

    rows = db.execute_query("SELECT * FROM cart_items WHERE id = ?", (cart_id,))
    assert len(rows) == 1
    assert rows[0]["dish_id"] == dish_id
    assert rows[0]["quantity"] == quantity
    


@pytest.mark.parametrize("name, price, quantity", [("购物车重复添加的菜", 38.0, 2)])
def test_add_to_cart_twice_accumulates(base_url, db, dish_factory, cart_factory, customer_ctx, name, price, quantity):
    """重复加入同一道菜：数量累加"""
    _, headers = customer_ctx()
    dish_id = dish_factory(name=name, price=price)
    cart_id_1 = cart_factory(dish_id=dish_id, quantity=quantity, headers=headers)
    cart_id_2 = cart_factory(dish_id=dish_id, quantity=quantity, headers=headers)

    assert cart_id_1 == cart_id_2, "同一道菜两次加入，cart_id 应该相同"

    rows = db.execute_query("SELECT quantity FROM cart_items WHERE id = ?", (cart_id_1,))
    assert rows[0]["quantity"] == quantity * 2, f"数量应该累加为 {quantity * 2}"


def test_add_to_cart_not_exist_dish(base_url, db, customer_ctx):
    """加入不存在的菜：404"""
    _, headers = customer_ctx()
    rows = db.execute_query("SELECT * FROM dishes WHERE id = 999999")
    assert len(rows) == 0

    res = requests.post(
        f"{base_url}/cart/items",
        json={"dish_id": 999999, "quantity": 1},
        headers=headers,
    )
    assert res.status_code == 404


def test_add_to_cart_off_shelf_dish(base_url, db, dish_factory, customer_ctx, merchant_ctx):
    """加入下架的菜：404"""
    _, headers = customer_ctx()
    _, merchant_h = merchant_ctx()
    dish_id = dish_factory(name="下架菜", price=10.0)

    r = requests.patch(f"{base_url}/dish/{dish_id}/status", json={"status": 0}, headers=merchant_h)
    assert r.status_code == 200

    rows = db.execute_query("SELECT status FROM dishes WHERE id = ?", (dish_id,))
    assert rows[0]["status"] == 0

    res = requests.post(
        f"{base_url}/cart/items",
        json={"dish_id": dish_id, "quantity": 1},
        headers=headers,
    )
    assert res.status_code == 404


def test_add_to_cart_soft_deleted_dish(base_url, db, dish_factory, customer_ctx, merchant_ctx):
    """加入软删除的菜：404"""
    _, headers = customer_ctx()
    _, merchant_h = merchant_ctx()
    dish_id = dish_factory(name="软删除菜", price=10.0)

    r = requests.delete(f"{base_url}/dish/{dish_id}", headers=merchant_h)
    assert r.status_code == 200

    rows = db.execute_query("SELECT is_deleted FROM dishes WHERE id = ?", (dish_id,))
    assert rows[0]["is_deleted"] == 1

    res = requests.post(
        f"{base_url}/cart/items",
        json={"dish_id": dish_id, "quantity": 1},
        headers=headers,
    )
    assert res.status_code == 404


@pytest.mark.parametrize("payload", [
    pytest.param({"dish_id": 1, "quantity": 0}, id="quantity_zero"),
    pytest.param({"dish_id": 1, "quantity": -1}, id="quantity_negative"),
    pytest.param({"dish_id": 0, "quantity": 1}, id="dish_id_zero"),
    pytest.param({"dish_id": 1}, id="quantity_missing"),
    pytest.param({"quantity": 1}, id="dish_id_missing"),
])
def test_add_to_cart_invalid_payload(base_url, customer_ctx, payload):
    """加入购物车：非法参数返回 422"""
    _, headers = customer_ctx()
    r = requests.post(f"{base_url}/cart/items", json=payload, headers=headers)
    assert r.status_code == 422


# ==================== 查询购物车 ====================

def test_get_cart_empty(base_url, customer_ctx):
    """购物车为空：返回 []"""
    _, headers = customer_ctx()
    r = requests.get(f"{base_url}/cart", headers=headers)

    assert r.status_code == 200
    assert isinstance(r.json()["data"], list)
    assert len(r.json()["data"]) == 0


def test_get_cart_with_items(base_url, db, dish_factory, cart_factory, customer_ctx):
    """购物车有数据：返回列表"""
    _, headers = customer_ctx()
    dish_id = dish_factory(name="宫保鸡丁", price=38.0)
    cart_id = cart_factory(dish_id=dish_id, quantity=2, headers=headers)

    rows = db.execute_query("SELECT * FROM cart_items WHERE id = ?", (cart_id,))
    assert len(rows) == 1

    r = requests.get(f"{base_url}/cart", headers=headers)
    assert r.status_code == 200
    data = r.json()["data"]
    item = next((d for d in data if d["cart_id"] == cart_id), None)
    assert item is not None
    assert item["dish_id"] == dish_id
    assert item["quantity"] == 2


def test_get_cart_with_off_shelf_dish(base_url, db, dish_factory, cart_factory, customer_ctx, merchant_ctx):
    """下架的菜仍显示在购物车"""
    _, headers = customer_ctx()
    _, merchant_h = merchant_ctx()
    dish_id = dish_factory(name="下架菜", price=10.0)
    cart_id = cart_factory(dish_id=dish_id, quantity=1, headers=headers)

    requests.patch(f"{base_url}/dish/{dish_id}/status", json={"status": 0}, headers=merchant_h)

    rows = db.execute_query("SELECT status FROM dishes WHERE id = ?", (dish_id,))
    assert rows[0]["status"] == 0

    r = requests.get(f"{base_url}/cart", headers=headers)
    data = r.json()["data"]
    item = next((d for d in data if d["cart_id"] == cart_id), None)
    assert item is not None
    assert item["dish_id"] == dish_id


def test_get_cart_with_soft_deleted_dish(base_url, db, dish_factory, cart_factory, customer_ctx, merchant_ctx):
    """软删除的菜仍显示在购物车"""
    _, headers = customer_ctx()
    _, merchant_h = merchant_ctx()
    dish_id = dish_factory(name="软删除菜", price=10.0)
    cart_id = cart_factory(dish_id=dish_id, quantity=1, headers=headers)

    requests.delete(f"{base_url}/dish/{dish_id}", headers=merchant_h)

    rows = db.execute_query("SELECT is_deleted FROM dishes WHERE id = ?", (dish_id,))
    assert rows[0]["is_deleted"] == 1

    r = requests.get(f"{base_url}/cart", headers=headers)
    data = r.json()["data"]
    item = next((d for d in data if d["cart_id"] == cart_id), None)
    assert item is not None
    assert item["dish_id"] == dish_id


# ==================== 修改数量 ====================

def test_update_cart_quantity_success(base_url, db, dish_factory, cart_factory, customer_ctx):
    """修改购物车数量成功"""
    _, headers = customer_ctx()
    dish_id = dish_factory(name="购物车修改菜", price=38.0)
    cart_id = cart_factory(dish_id=dish_id, quantity=2, headers=headers)

    rows = db.execute_query("SELECT quantity FROM cart_items WHERE id = ?", (cart_id,))
    assert rows[0]["quantity"] == 2

    r = requests.put(f"{base_url}/cart/items/{cart_id}", json={"quantity": 5}, headers=headers)
    assert r.status_code == 200
    assert r.json()["data"]["cart_id"] == cart_id
    assert r.json()["data"]["new_quantity"] == 5

    rows = db.execute_query("SELECT quantity FROM cart_items WHERE id = ?", (cart_id,))
    assert rows[0]["quantity"] == 5


def test_update_cart_quantity_not_exist(base_url, db, customer_ctx):
    """修改不存在的购物车项：404"""
    _, headers = customer_ctx()
    rows = db.execute_query("SELECT * FROM cart_items WHERE id = 99999")
    assert len(rows) == 0

    r = requests.put(f"{base_url}/cart/items/99999", json={"quantity": 5}, headers=headers)
    assert r.status_code == 404


@pytest.mark.parametrize("payload", [
    pytest.param({"quantity": 0}, id="quantity_zero"),
    pytest.param({"quantity": -1}, id="quantity_negative"),
    pytest.param({"quantity": "abc"}, id="quantity_wrong_type"),
    pytest.param({}, id="quantity_missing"),
])
def test_update_cart_quantity_invalid(base_url, dish_factory, cart_factory, customer_ctx, payload):
    """修改数量：非法参数返回 422"""
    _, headers = customer_ctx()
    dish_id = dish_factory(name="修改购物车不合规范输入的菜", price=38.0)
    cart_id = cart_factory(dish_id=dish_id, quantity=2, headers=headers)

    r = requests.put(f"{base_url}/cart/items/{cart_id}", json=payload, headers=headers)
    assert r.status_code == 422


# ==================== 删除 ====================

def test_delete_cart_item_success(base_url, db, dish_factory, cart_factory, customer_ctx):
    """删除购物车项成功"""
    _, headers = customer_ctx()
    dish_id = dish_factory(name="购物车删除成功菜", price=38.0)
    cart_id = cart_factory(dish_id=dish_id, quantity=2, headers=headers)

    rows = db.execute_query("SELECT * FROM cart_items WHERE id = ?", (cart_id,))
    assert len(rows) == 1

    r = requests.delete(f"{base_url}/cart/items/{cart_id}", headers=headers)
    assert r.status_code == 200
    assert r.json()["data"]["cart_id"] == cart_id

    rows = db.execute_query("SELECT * FROM cart_items WHERE id = ?", (cart_id,))
    assert len(rows) == 0


def test_delete_cart_item_twice(base_url, dish_factory, cart_factory, customer_ctx):
    """重复删除：第二次返回 404"""
    _, headers = customer_ctx()
    dish_id = dish_factory(name="重复删除菜", price=38.0)
    cart_id = cart_factory(dish_id=dish_id, quantity=2, headers=headers)

    r1 = requests.delete(f"{base_url}/cart/items/{cart_id}", headers=headers)
    assert r1.status_code == 200

    r2 = requests.delete(f"{base_url}/cart/items/{cart_id}", headers=headers)
    assert r2.status_code == 404


def test_delete_cart_item_not_exist(base_url, db, customer_ctx):
    """删除不存在的购物车项：404"""
    _, headers = customer_ctx()
    rows = db.execute_query("SELECT * FROM cart_items WHERE id = 99999")
    assert len(rows) == 0

    r = requests.delete(f"{base_url}/cart/items/99999", headers=headers)
    assert r.status_code == 404


# ==================== 权限测试 ====================

def test_cart_without_token(base_url):
    """未登录 401"""
    r = requests.get(f"{base_url}/cart")
    assert r.status_code == 401


def test_cart_with_invalid_token(base_url):
    """无效 token 401"""
    r = requests.get(f"{base_url}/cart", headers={"Authorization": "Bearer invalid_token"})
    assert r.status_code == 401


def test_cart_with_merchant_token(base_url, merchant_ctx):
    """商户访问顾客接口 403"""
    _, merchant_h = merchant_ctx()
    r = requests.get(f"{base_url}/cart", headers=merchant_h)
    assert r.status_code == 403