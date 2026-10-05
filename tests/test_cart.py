"""购物车测试（Part 6）"""
import requests
import pytest

#加入购物车
#1、正确加入购物车
#2、加入不存在的菜品
#3、加入已下架的菜品
#4、加入已软删除的菜品
#5、加入已存在的菜品（更新数量）
#6、加入数量为0或负数
#7、加入数量为非整数

#查询购物车
#1、查询购物车成功
#2、查询购物测为空看返回的数据容器是否为列表
#3、查询购物车中有已下架的菜品，是否能查到
#4、查询购物车中有已软删除的菜品，是否能查到    


#修改购物车数量
#1、修改购物车数量成功
#2、修改购物车数量为0或负数
#3、修改购物车数量为非整数
#4、修改购物车中不存在的菜品


#删除购物车中的菜品
#1、删除购物车中的菜品成功
#2、删除购物车中不存在的菜品

# ==================== 加入购物车 ====================
@pytest.mark.parametrize("name, price, quantity", [("加入购物车的菜", 6.0, 2)])
def test_add_to_cart_success(base_url, db, dish_factory, cart_factory, name, price, quantity):
    """正确加入购物车"""
    # 1. 创建菜品
    dish_id = dish_factory(name=name, price=price)
    
    # 2. 加入购物车
    cart_id = cart_factory(dish_id=dish_id, quantity=quantity)
    assert cart_id is not None
    
    # 3. 验证接口返回
    res = requests.get(f"{base_url}/cart")
    assert res.status_code == 200
    data = res.json()["data"]
    item = next((d for d in data if d["dish_id"] == dish_id), None)#从购物车列表里，找到 dish_id 匹配的那一项。#取生成器的第一个匹配项；如果没有，返回 None
    assert item is not None, "购物车里应该有这个菜品"
    assert item["quantity"] == quantity
    
    # 4. 验证数据库落库
    rows = db.execute_query("SELECT * FROM cart_items WHERE id = ?", (cart_id,))
    assert len(rows) == 1
    assert rows[0]["dish_id"] == dish_id
    assert rows[0]["quantity"] == quantity



@pytest.mark.parametrize("name, price, quantity", [
    ("购物车重复添加的菜", 38.0, 2),
])
def test_add_to_cart_twice_accumulates(base_url, db, dish_factory, cart_factory, name, price, quantity):
    """重复加入同一道菜：数量累加"""
    # 1. 创建菜品
    dish_id = dish_factory(name=name, price=price)
    
    # 2. 第一次加入
    cart_id_1 = cart_factory(dish_id=dish_id, quantity=quantity)
    
    # 3. 第二次加入（同一道菜）
    cart_id_2 = cart_factory(dish_id=dish_id, quantity=quantity)
    
    # 4. 核心断言 1：cart_id 相同
    assert cart_id_1 == cart_id_2, "同一道菜两次加入，cart_id 应该相同"
    
    # 5. 核心断言 2：数量累加
    rows = db.execute_query("SELECT quantity FROM cart_items WHERE id = ?", (cart_id_1,))
    assert rows[0]["quantity"] == quantity * 2, f"数量应该累加为 {quantity * 2}"



    
def test_add_to_cart_not_exist_dish(db,base_url):         # 加入不存在的菜
    rows = db.execute_query("SELECT * FROM dishes WHERE id = 999999")
    assert len(rows) == 0, "前置条件：id=999999 不应存在"
    res = requests.post(
    f"{base_url}/cart/items",
    json={"dish_id": 999999, "quantity": 1},
)
    assert res.status_code == 404

def test_add_to_cart_off_shelf_dish(base_url, db, dish_factory):
    """加入下架的菜：404"""
    # 1. 创建菜品
    dish_id = dish_factory(name="下架菜", price=10.0)
    
    # 2. 下架
    r = requests.patch(f"{base_url}/dish/{dish_id}/status", json={"status": 0})
    assert r.status_code == 200, f"下架失败：{r.text}"
    
    # 3. 验证数据库里 status=0
    rows = db.execute_query("SELECT status FROM dishes WHERE id = ?", (dish_id,))
    assert rows[0]["status"] == 0, "菜品应该已下架"
    
    # 4. 加入购物车
    res = requests.post(
        f"{base_url}/cart/items",
        json={"dish_id": dish_id, "quantity": 1},
    )
    
    # 5. 断言 404
    assert res.status_code == 404, f"加入下架的菜应该返回 404：{res.text}"


def test_add_to_cart_soft_deleted_dish(base_url, db, dish_factory):
    """加入软删除的菜：404"""
    # 1. 创建菜品
    dish_id = dish_factory(name="软删除菜", price=10.0)
    
    # 2. 软删除
    r = requests.delete(f"{base_url}/dish/{dish_id}")
    assert r.status_code == 200, f"软删除失败：{r.text}"
    
    # 3. 验证数据库里 is_deleted=1
    rows = db.execute_query("SELECT is_deleted FROM dishes WHERE id = ?", (dish_id,))
    assert rows[0]["is_deleted"] == 1, "菜品应该已软删除"
    
    # 4. 加入购物车
    res = requests.post(
        f"{base_url}/cart/items",
        json={"dish_id": dish_id, "quantity": 1},
    )
    
    # 5. 断言 404
    assert res.status_code == 404, f"加入软删除的菜应该返回 404：{res.text}"

@pytest.mark.parametrize("payload", [
    pytest.param({"dish_id": 1, "quantity": 0}, id="quantity_zero"),
    pytest.param({"dish_id": 1, "quantity": -1}, id="quantity_negative"),
    pytest.param({"dish_id": 0, "quantity": 1}, id="dish_id_zero"),
    pytest.param({"dish_id": 1}, id="quantity_missing"),
    pytest.param({"quantity": 1}, id="dish_id_missing"),
])
def test_add_to_cart_invalid_payload(base_url, payload):
    """加入购物车：非法参数返回 422"""
    r = requests.post(f"{base_url}/cart/items", json=payload)
    assert r.status_code == 422



# ==================== 查询购物车 ====================

def test_get_cart_empty(base_url, db):
    """购物车为空：返回 []"""
    # 前置条件：清空购物车
    db.execute_update("DELETE FROM cart_items")
    
    # 调用接口
    r = requests.get(f"{base_url}/cart")
    
    # 断言
    assert r.status_code == 200
    assert isinstance(r.json()["data"], list), "data 必须是 list"
    assert len(r.json()["data"]) == 0, "购物车应该为空"

def test_get_cart_with_items(base_url, db, dish_factory, cart_factory):
    """购物车有数据：返回列表"""
    dish_id = dish_factory(name="宫保鸡丁", price=38.0)
    cart_id = cart_factory(dish_id=dish_id, quantity=2)
    
    # 前置条件：验证购物车里有数据
    rows = db.execute_query("SELECT * FROM cart_items WHERE id = ?", (cart_id,))
    assert len(rows) == 1
    
    # 查询购物车
    r = requests.get(f"{base_url}/cart")
    assert r.status_code == 200
    data = r.json()["data"]
    item = next((d for d in data if d["cart_id"] == cart_id), None)
    assert item is not None
    assert item["dish_id"] == dish_id
    assert item["quantity"] == 2


def test_get_cart_with_off_shelf_dish(base_url, db, dish_factory, cart_factory):
    """下架的菜仍显示在购物车"""
    dish_id = dish_factory(name="下架菜", price=10.0)
    cart_id = cart_factory(dish_id=dish_id, quantity=1)
    
    # 下架
    requests.patch(f"{base_url}/dish/{dish_id}/status", json={"status": 0})
    
    # 验证下架成功
    rows = db.execute_query("SELECT status FROM dishes WHERE id = ?", (dish_id,))
    assert rows[0]["status"] == 0
    
    # 查询购物车
    r = requests.get(f"{base_url}/cart")
    data = r.json()["data"]
    item = next((d for d in data if d["cart_id"] == cart_id), None)
    assert item is not None, "下架的菜仍应显示在购物车"
    assert item["dish_id"] == dish_id


def test_get_cart_with_soft_deleted_dish(base_url, db, dish_factory, cart_factory):
    """软删除的菜仍显示在购物车"""
    dish_id = dish_factory(name="软删除菜", price=10.0)
    cart_id = cart_factory(dish_id=dish_id, quantity=1)
    
    # 软删除
    requests.delete(f"{base_url}/dish/{dish_id}")
    
    # 验证软删除成功
    rows = db.execute_query("SELECT is_deleted FROM dishes WHERE id = ?", (dish_id,))
    assert rows[0]["is_deleted"] == 1
    
    # 查询购物车
    r = requests.get(f"{base_url}/cart")
    data = r.json()["data"]
    item = next((d for d in data if d["cart_id"] == cart_id), None)
    assert item is not None, "软删除的菜仍应显示在购物车"
    assert item["dish_id"] == dish_id


# ==================== 修改数量 ====================

def test_update_cart_quantity_success(base_url, db, dish_factory, cart_factory):
    """修改购物车数量成功"""
    # 前置条件：创建菜品 + 加入购物车
    dish_id = dish_factory(name="购物车修改菜", price=38.0)
    cart_id = cart_factory(dish_id=dish_id, quantity=2)
    
    # 验证前置条件
    rows = db.execute_query("SELECT quantity FROM cart_items WHERE id = ?", (cart_id,))
    assert rows[0]["quantity"] == 2
    
    # 改数量
    r = requests.put(f"{base_url}/cart/items/{cart_id}", json={"quantity": 5})
    assert r.status_code == 200, f"修改失败：{r.text}"
    
    # 验证接口返回
    assert r.json()["data"]["cart_id"] == cart_id
    assert r.json()["data"]["new_quantity"] == 5
    
    # 验证数据库落库
    rows = db.execute_query("SELECT quantity FROM cart_items WHERE id = ?", (cart_id,))
    assert rows[0]["quantity"] == 5, "数据库里数量应该更新为 5"

def test_update_cart_quantity_not_exist(base_url, db):
    """修改不存在的购物车项：404"""
    # 前置条件：确认这个 cart_id 不存在
    rows = db.execute_query("SELECT * FROM cart_items WHERE id = 99999")
    assert len(rows) == 0, "前置条件：id=99999 不应存在"
    
    # 改数量
    r = requests.put(f"{base_url}/cart/items/99999", json={"quantity": 5})
    assert r.status_code == 404, f"不存在的购物车项应返回 404：{r.text}"


@pytest.mark.parametrize("payload", [
    pytest.param({"quantity": 0}, id="quantity_zero"),
    pytest.param({"quantity": -1}, id="quantity_negative"),
    pytest.param({"quantity": "abc"}, id="quantity_wrong_type"),
    pytest.param({}, id="quantity_missing"),
])
def test_update_cart_quantity_invalid(base_url, dish_factory, cart_factory, payload):
    """修改数量：非法参数返回 422"""
    # 前置条件：创建菜品 + 加入购物车
    dish_id = dish_factory(name="修改购物车不合规范输入的菜", price=38.0)
    cart_id = cart_factory(dish_id=dish_id, quantity=2)
    
    # 改数量（非法参数）
    r = requests.put(f"{base_url}/cart/items/{cart_id}", json=payload)
    assert r.status_code == 422, f"非法参数应返回 422：{r.text}"

# ==================== 删除 ====================

def test_delete_cart_item_success(base_url, db, dish_factory, cart_factory):
    """删除购物车项成功"""
    # 前置条件：创建菜品 + 加入购物车
    dish_id = dish_factory(name="购物车删除成功菜", price=38.0)
    cart_id = cart_factory(dish_id=dish_id, quantity=2)
    
    # 验证前置条件：购物车项存在
    rows = db.execute_query("SELECT * FROM cart_items WHERE id = ?", (cart_id,))
    assert len(rows) == 1, "前置条件：购物车项应该存在"
    
    # 删除
    r = requests.delete(f"{base_url}/cart/items/{cart_id}")
    assert r.status_code == 200, f"删除失败：{r.text}"
    assert r.json()["data"]["cart_id"] == cart_id
    
    # 验证数据库里记录没了
    rows = db.execute_query("SELECT * FROM cart_items WHERE id = ?", (cart_id,))
    assert len(rows) == 0, "删除后数据库里不应该有这条记录"


def test_delete_cart_item_twice(base_url, dish_factory, cart_factory):
    """重复删除：第二次返回 404"""
    # 前置条件：创建菜品 + 加入购物车
    dish_id = dish_factory(name="重复删除菜", price=38.0)
    cart_id = cart_factory(dish_id=dish_id, quantity=2)
    
    # 第一次删除成功
    r1 = requests.delete(f"{base_url}/cart/items/{cart_id}")
    assert r1.status_code == 200, f"第一次删除失败：{r1.text}"
    
    # 第二次删除应该 404
    r2 = requests.delete(f"{base_url}/cart/items/{cart_id}")
    assert r2.status_code == 404, f"重复删除应该返回 404：{r2.text}"


def test_delete_cart_item_not_exist(base_url, db):
    """删除不存在的购物车项：404"""
    # 前置条件：确认这个 cart_id 不存在
    rows = db.execute_query("SELECT * FROM cart_items WHERE id = 99999")
    assert len(rows) == 0, "前置条件：id=99999 不应存在"
    
    # 删除
    r = requests.delete(f"{base_url}/cart/items/99999")
    assert r.status_code == 404, f"不存在的购物车项应返回 404：{r.text}"