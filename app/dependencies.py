"""依赖注入（Part 11.3）"""
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer
from app.auth import decode_jwt


security = HTTPBearer()


def get_current_user(credentials = Depends(security)):
    """解析 token，返回用户信息"""
    token = credentials.credentials
    payload = decode_jwt(token)
    if not payload:
        raise HTTPException(status_code=401, detail="无效令牌")
    return payload   # {"user_id": 1, "role": "customer"}


def get_current_customer(current_user = Depends(get_current_user)):
    """检查 role 是否是 customer"""
    if current_user["role"] != "customer":
        raise HTTPException(status_code=403, detail="只有顾客能操作")
    return current_user


def get_current_merchant(current_user = Depends(get_current_user)):
    """检查 role 是否是 merchant"""
    if current_user["role"] != "merchant":
        raise HTTPException(status_code=403, detail="只有商户能操作")
    return current_user