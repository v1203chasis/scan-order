#描述"一个请求/响应里的数据，应该有哪些字段、什么类型、有什么约束"。

from pydantic import BaseModel, Field


class DishCreate(BaseModel):
    name: str = Field(..., min_length=1)
    price: float = Field(..., gt=0)



class DishUpdate(BaseModel):
    price: float = Field(..., gt=0)


'''购物车的pydantic模型'''
class CartItemCreate(BaseModel):
    """加入购物车请求体"""
    dish_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0)


class CartQuantityUpdate(BaseModel):
    """修改数量请求体"""
    quantity: int = Field(..., gt=0)