import pytest
import requests
import uuid
import os

BASE_URL = "http://127.0.0.1:8000"

def pytest_addoption(parser):
    parser.addoption(
        "--env",
        action="store",
        default="dev",
        help="指定测试环境：dev / test",
    )


@pytest.fixture(scope="session", autouse=True)
def set_env(request):
    """根据 --env 设置环境变量"""
    env = request.config.getoption("--env")

    env_map = {
        "dev": {
            "DB_PATH": "scan_order.db",
            "BASE_URL": "http://127.0.0.1:8000",
            "SECRET_KEY": "dev-secret-key-that-is-at-least-32-bytes-long",
        },
        "test": {
            "DB_PATH": "test_scan_order.db",
            "BASE_URL": "http://127.0.0.1:8000",
            "SECRET_KEY": "test-secret-key-that-is-at-least-32-bytes-long",
        },
    }

    config = env_map[env]
    for key, value in config.items():
        os.environ[key] = value



@pytest.fixture(scope="session", autouse=True)
#一次会话(一次 pytest 运行)使用一次（因为scope='session'
#autouse=True 让pytest自动使用这个fixture（测试函数不用声明）
def setup_test_db():
    """测试会话开始前建库"""
    from app.db_helper import init_db
    init_db()
    yield
    # 不删库（避免文件占用问题）

@pytest.fixture(autouse=True)
#执行频率每个测试(测试函数	def test_xxx(): 一个函数)前一次,
def clean_db():
    """每个测试前清空所有表"""
    from app import db_helper
    #要先引入中国db_helper模块才能使用它的内部函数（引用它的功能把他绑在这里）
    # setup：先清空
    db_helper.execute_update("DELETE FROM payments")
    db_helper.execute_update("DELETE FROM order_items")
    db_helper.execute_update("DELETE FROM orders")
    db_helper.execute_update("DELETE FROM cart_items")
    db_helper.execute_update("DELETE FROM dishes")
    db_helper.execute_update("DELETE FROM users") 
    yield
'''
clean_db 是 autouse=True 的 fixture，会被每个测试自动调用。

如果没有 autouse=True，只有测试声明它时才执行。
'''

@pytest.fixture(scope="session")
def base_url():
    return BASE_URL


@pytest.fixture(scope="session")
#测试函数要"拿返回值"，必须声明（def test_xxx(db)），所以不使用autouse=True
def db():
    from app import db_helper
    return db_helper
#这个是为了全局化使用这个功能,让pytest自动注入
'''
# test_xxx.py
def test_xxx(db):   # ← pytest 自动注入 db
    rows = db.execute_query("SELECT ...")
'''


@pytest.fixture
def dish_factory(base_url, db,merchant_ctx):
    created_ids = []

    def create_dish(name: str = None, price: float = 10.0) -> int:
        if name is None:
            name = f"测试菜_{uuid.uuid4().hex[:8]}"
        _, headers = merchant_ctx()  
        r = requests.post(f"{base_url}/dish", json={"name": name, "price": price},headers=headers)
        assert r.status_code == 200, f"factory 创建菜品失败：{r.text}"
        dish_id = r.json()["data"]["id"]
        created_ids.append(dish_id)
        return dish_id

    yield create_dish

    for dish_id in reversed(created_ids):
        db.execute_update("DELETE FROM dishes WHERE id = ?", (dish_id,))


@pytest.fixture#这个是加入购物车啊喂，就是如果你想将其他菜品加入到这个用户的购物车里面，就要填入这个用户的headers
def cart_factory(base_url, db, customer_ctx):#customer_headers这是个获取token并拼成header的函数
    created_cart_ids = []

    def create_cart_item(dish_id: int, quantity: int = 1, headers: dict = None) -> int:
        if headers is None:
            _, headers = customer_ctx()   # ← 默认用新顾客（为了测试隔离）
        r = requests.post(
            f"{base_url}/cart/items",
            json={"dish_id": dish_id, "quantity": quantity},
            headers=headers,   # ← 带 token
        )
        assert r.status_code == 200, f"factory 加入购物车失败：{r.text}"
        cart_id = r.json()["data"]["cart_id"]
        created_cart_ids.append(cart_id)
        return cart_id

    yield create_cart_item

    for cart_id in reversed(created_cart_ids):
        db.execute_update("DELETE FROM cart_items WHERE id = ?", (cart_id,))


@pytest.fixture
def order_factory(base_url, db, customer_ctx):
    created_order_ids = []

    def create_order(headers: dict = None):
        if headers is None:
            _, headers = customer_ctx()
        r = requests.post(f"{base_url}/orders", headers=headers)
        assert r.status_code == 200, f"factory 下单失败：{r.text}"
        order_id = r.json()["data"]["order_id"]
        created_order_ids.append(order_id)
        return order_id

    yield create_order

    for order_id in created_order_ids:
        db.execute_update("DELETE FROM payments WHERE order_id = ?", (order_id,))
        db.execute_update("DELETE FROM order_items WHERE order_id = ?", (order_id,))
        db.execute_update("DELETE FROM orders WHERE id = ?", (order_id,))


@pytest.fixture
def user_factory(base_url, db):
    created_ids = []

    def create_user(username: str = None, password: str = "123456", role: str = "customer"):
        if username is None:
            username = f"测试用户_{uuid.uuid4().hex[:8]}"
        r = requests.post(
            f"{base_url}/register",
            json={"username": username, "password": password, "role": role},
        )
        assert r.status_code == 200, f"factory 创建用户失败：{r.text}"
        user_id = r.json()["data"]["user_id"]
        created_ids.append(user_id)
        return {"user_id": user_id, "username": username, "password": password, "role": role}

    yield create_user

    for user_id in reversed(created_ids):
        db.execute_update("DELETE FROM users WHERE id = ?", (user_id,))

@pytest.fixture
def login(base_url):
    def _login(username, password):
        r = requests.post(f"{base_url}/login", json={"username": username, "password": password})
        assert r.status_code == 200, f"登录失败：{r.text}"
        return r.json()["data"]["token"]
    return _login

'''
@pytest.fixture
def customer_headers(user_factory, login):
    def _get_headers():
        user = user_factory(role="customer")#user = {"user_id": user_id, "username": username, "password": password, "role": role}
        token = login(user["username"], user["password"])
        return {"Authorization": f"Bearer {token}"}
    return _get_headers



@pytest.fixture
def merchant_headers(user_factory, login):   # ← 加 login
    def _get_headers():
        user = user_factory(role="merchant")
        token = login(user["username"], user["password"])   # ← 复用
        return {"Authorization": f"Bearer {token}"}
    return _get_headers
'''
@pytest.fixture
def customer_ctx(user_factory, login):
    """返回 (user_id, headers)"""
    def _get_ctx():
        user = user_factory(role="customer")
        token = login(user["username"], user["password"])
        headers = {"Authorization": f"Bearer {token}"}
        return user["user_id"], headers
    return _get_ctx


@pytest.fixture
def merchant_ctx(user_factory, login):
    """返回 (user_id, headers)"""
    def _get_ctx():
        user = user_factory(role="merchant")
        token = login(user["username"], user["password"])
        headers = {"Authorization": f"Bearer {token}"}
        return user["user_id"], headers
    return _get_ctx



