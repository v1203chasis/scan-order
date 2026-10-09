"""JWT 和密码工具"""
import jwt
import bcrypt
from datetime import datetime, timedelta
from app.config import config


# ==================== 密码哈希 ====================
#作用：接收明文密码，返回哈希
def hash_password(password: str) -> str:
    """密码哈希（bcrypt）"""
    salt = bcrypt.gensalt()#生成“盐”（随机字符串）
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)#password.encode("utf-8")把字符串转成“字节”（bcrypt需要字节）
    return hashed.decode("utf-8")#hashed.decode("utf-8")把字节转回字符串


def verify_password(password: str, hashed: str) -> bool:#返回值是布尔值哦！
    """验证密码"""
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    #password.encode("utf-8")：明文转字节。（这个password是用户登录输入进来的吧）
    #hashed.encode("utf-8")：哈希转字节。（这个又是哪里来的）
    #bcrypt.checkpw(明文, 哈希)：比对。
    '''bcrypt.checkpw 做什么？
         从 hashed 里提取 salt。
        用同样的 salt + password 重新哈希。
        比对结果。
        关键：不是"解密"，是"重新计算 + 比对"。
    '''

# ==================== JWT ====================

def create_jwt(user_id: int, role: str, expires_hours: int = 24) -> str:
    """生成 JWT"""
    payload = {
        "user_id": user_id,
        "role": role,
        "exp": datetime.utcnow() + timedelta(hours=expires_hours)
    }
    return jwt.encode(payload, config.SECRET_KEY, algorithm="HS256")
'''
jwt.encode(payload, key, algorithm)：

payload：要编码的数据。

config.SECRET_KEY：签名密钥。

algorithm="HS256"：签名算法。
'''


def decode_jwt(token: str):
    """解析 JWT，成功返回 payload，失败返回 None"""
    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        return None   # 过期
    except jwt.InvalidTokenError:
        return None   # 无效