import pytest
import requests
import uuid

BASE_URL = "http://127.0.0.1:8000"


@pytest.fixture(scope="session")
def base_url():
    return BASE_URL


@pytest.fixture(scope="session")
def db():
    from app import db_helper
    return db_helper


@pytest.fixture
def dish_factory(base_url, db):
    created_ids = []
    
    def create_dish(name: str = None, price: float = 10.0) -> int:
        if name is None:
            name = f"测试菜_{uuid.uuid4().hex[:8]}"
        r = requests.post(f"{base_url}/dish", json={"name": name, "price": price})
        assert r.status_code == 200, f"factory 创建菜品失败：{r.text}"
        dish_id = r.json()["data"]["id"]
        created_ids.append(dish_id)
        return dish_id
    
    yield create_dish
    
    for dish_id in reversed(created_ids):
        db.execute_update("DELETE FROM dishes WHERE id = ?", (dish_id,))


@pytest.fixture
def cart_factory(base_url, db):
    """创建购物车项，测试结束后清理"""
    created_cart_ids = []
    
    def create_cart_item(dish_id: int, quantity: int = 1) -> int:
        r = requests.post(
            f"{base_url}/cart/items",
            json={"dish_id": dish_id, "quantity": quantity},
        )
        assert r.status_code == 200, f"factory 加入购物车失败：{r.text}"
        cart_id = r.json()["data"]["cart_id"]
        created_cart_ids.append(cart_id)
        return cart_id
    
    yield create_cart_item
    
    for cart_id in reversed(created_cart_ids):
        db.execute_update("DELETE FROM cart_items WHERE id = ?", (cart_id,))


@pytest.fixture
def order_factory(base_url, db):
    """创建订单（从购物车），测试结束后清理"""
    created_order_ids = []

    def create_order():
        r = requests.post(f"{base_url}/orders")
        assert r.status_code == 200, f"factory 下单失败：{r.text}"
        order_id = r.json()["data"]["order_id"]
        created_order_ids.append(order_id)
        return order_id

    yield create_order

    # 清理：先删 payments，再删 order_items，最后删 orders
    for order_id in created_order_ids:
        db.execute_update("DELETE FROM payments WHERE order_id = ?", (order_id,))
        db.execute_update("DELETE FROM order_items WHERE order_id = ?", (order_id,))
        db.execute_update("DELETE FROM orders WHERE id = ?", (order_id,))


def load_yaml(file_path):
    import os
    import yaml
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    full_path = os.path.join(base_dir, file_path)
    with open(full_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


    