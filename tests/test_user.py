"""用户测试（Part 11.1）"""
import requests
import pytest


# ==================== 注册 ====================

def test_register_success(base_url, db):
    """注册成功"""
    r = requests.post(
        f"{base_url}/register",
        json={"username": "张三", "password": "123456", "role": "customer"},
    )
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["username"] == "张三"
    assert data["role"] == "customer"

    rows = db.execute_query("SELECT username, role FROM users WHERE id = ?", (data["user_id"],))
    assert len(rows) == 1
    assert rows[0]["username"] == "张三"
    assert rows[0]["role"] == "customer"


def test_register_duplicate_username(base_url, user_factory):
    """重复用户名：400"""
    user_factory(username="张三")
    r = requests.post(
        f"{base_url}/register",
        json={"username": "张三", "password": "123456", "role": "customer"},
    )
    assert r.status_code == 400


# 参数校验：注册
@pytest.mark.parametrize("payload", [
    pytest.param({"username": "", "password": "123456", "role": "customer"}, id="username_empty"),
    pytest.param({"username": "a"*51, "password": "123456", "role": "customer"}, id="username_too_long"),
    pytest.param({"password": "123456", "role": "customer"}, id="username_missing"),
    pytest.param({"username": "张三", "password": "", "role": "customer"}, id="password_empty"),
    pytest.param({"username": "张三", "password": "a"*101, "role": "customer"}, id="password_too_long"),
    pytest.param({"username": "张三", "role": "customer"}, id="password_missing"),
    pytest.param({"username": "张三", "password": "123456", "role": "admin"}, id="role_invalid"),
    pytest.param({"username": "张三", "password": "123456", "role": ""}, id="role_empty"),
    pytest.param({"username": "张三", "password": "123456"}, id="role_missing"),
])
def test_register_invalid_payload(base_url, payload):
    """注册：非法参数 422"""
    r = requests.post(f"{base_url}/register", json=payload)
    assert r.status_code == 422


# ==================== 登录 ====================

def test_login_success(base_url, user_factory):
    """登录成功"""
    user_factory(username="张三", password="123456", role="customer")
    r = requests.post(
        f"{base_url}/login",
        json={"username": "张三", "password": "123456"},
    )
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["username"] == "张三"
    assert data["role"] == "customer"
    assert "token" in data   # ← 加这行
    assert len(data["token"]) > 0   # ← 加这行   


def test_login_wrong_password(base_url, user_factory):
    """密码错误：401"""
    user_factory(username="张三", password="123456")
    r = requests.post(
        f"{base_url}/login",
        json={"username": "张三", "password": "wrong"},
    )
    assert r.status_code == 401


def test_login_user_not_exist(base_url):
    """用户不存在：401"""
    r = requests.post(
        f"{base_url}/login",
        json={"username": "不存在", "password": "123456"},
    )
    assert r.status_code == 401


# 参数校验：登录
@pytest.mark.parametrize("payload", [
    pytest.param({"username": "", "password": "123456"}, id="username_empty"),
    pytest.param({"username": "a"*51, "password": "123456"}, id="username_too_long"),
    pytest.param({"password": "123456"}, id="username_missing"),
    pytest.param({"username": "张三", "password": ""}, id="password_empty"),
    pytest.param({"username": "张三", "password": "a"*101}, id="password_too_long"),
    pytest.param({"username": "张三"}, id="password_missing"),
])
def test_login_invalid_payload(base_url, payload):
    """登录：非法参数 422"""
    r = requests.post(f"{base_url}/login", json=payload)
    assert r.status_code == 422


# ==================== 完整流程 ====================

def test_register_and_login(base_url):
    """注册后能登录"""
    r1 = requests.post(
        f"{base_url}/register",
        json={"username": "李四", "password": "abc123", "role": "merchant"},
    )
    assert r1.status_code == 200

    r2 = requests.post(
        f"{base_url}/login",
        json={"username": "李四", "password": "abc123"},
    )
    assert r2.status_code == 200
    assert r2.json()["data"]["role"] == "merchant"