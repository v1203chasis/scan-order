"""JWT 和密码工具测试"""
from app.auth import hash_password, verify_password, create_jwt, decode_jwt


# ==================== 密码哈希 ====================

def test_hash_password():
    """密码哈希"""
    hashed = hash_password("123456")
    assert hashed != "123456"
    assert hashed.startswith("$2b$")   # bcrypt 格式


def test_verify_password_correct():
    """正确密码验证成功"""
    hashed = hash_password("123456")
    assert verify_password("123456", hashed) is True


def test_verify_password_wrong():
    """错误密码验证失败"""
    hashed = hash_password("123456")
    assert verify_password("wrong", hashed) is False


# ==================== JWT ====================

def test_create_jwt():
    """生成 JWT"""
    token = create_jwt(1, "customer")
    assert isinstance(token, str)
    assert len(token) > 0
    assert token.count(".") == 2   # JWT 三段


def test_decode_jwt():
    """解析 JWT"""
    token = create_jwt(1, "customer")
    payload = decode_jwt(token)
    assert payload is not None
    assert payload["user_id"] == 1
    assert payload["role"] == "customer"


def test_decode_jwt_invalid():
    """无效 token"""
    assert decode_jwt("invalid_token") is None


def test_decode_jwt_expired():
    """过期 token"""
    token = create_jwt(1, "customer", expires_hours=-1)   # 已过期
    assert decode_jwt(token) is None