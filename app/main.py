from fastapi import FastAPI
from app.db_helper import init_db
from app.models import DishCreate
from app.crud import crud_dish
from fastapi import FastAPI, HTTPException 
from fastapi import Path,Body,Depends
from pydantic import BaseModel, Field
from app.dependencies import get_current_user, get_current_customer, get_current_merchant

app = FastAPI(title="Scan Order API")


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/health")
def health():
    return {"code": 200, "msg": "ok"}
  

@app.post("/dish")
def create_dish(req: DishCreate):
    # 业务规则：菜名不能重复
    existing = crud_dish.get_dish_by_name(req.name)
    if existing:
        raise HTTPException(status_code=400, detail="菜名已存在")
    
    new_id = crud_dish.create_dish(req.name,req.price)
    dish = crud_dish.get_dish_by_id(new_id)
    return {
            "id":new_id,
            "msg":"添加新菜品成功！",
            "data":dish,
            }

# ==================== 商户视角 ====================

@app.get("/dish/name/{name}")   # ← 具体路由在前
def get_dish_by_name_api(name: str = Path(..., min_length=1, max_length=50)):
    """商户视角：按菜名查（用于调试或前端搜索）"""
    dish = crud_dish.get_dish_by_name(name)
    if not dish:
        raise HTTPException(status_code=404, detail="菜品不存在")
    return {"msg": "获取成功", "data": dish}


@app.get("/dish/{dish_id}")   # ← 通用路由在后
def get_dish_by_id_api(dish_id: int = Path(..., gt=0)):
    """商户视角：按 ID 查菜（能看到下架的）"""
    dish = crud_dish.get_dish_by_id(dish_id)
    if not dish:
        raise HTTPException(status_code=404, detail="菜品不存在")
    return {"msg": "获取成功", "data": dish}


@app.get("/dishes")
def get_all_dishes_api():
    """商户视角：查所有菜（包括下架的）"""
    dishes = crud_dish.get_all_dishes()
    return {"msg": "获取成功", "data": dishes}


# ==================== 顾客视角 ====================

@app.get("/menu/dish/{dish_id}")
def get_dish_for_customer(dish_id: int = Path(..., gt=0)):
    """顾客视角：按 ID 查上架的菜"""
    dish = crud_dish.get_available_dish_by_id(dish_id)
    if not dish:
        raise HTTPException(status_code=404, detail="菜品不存在或已下架")
    return {"msg": "获取成功", "data": dish}


@app.get("/menu")
def get_menu_for_customer():
    """顾客视角：查菜单列表（只显示上架的）"""
    dishes = crud_dish.get_available_dishes()
    return {"msg": "获取成功", "data": dishes}


from app.models import DishUpdate, DishCreate

@app.put("/dish/{dish_id}")
def put_dish_by_id(
    dish_id: int = Path(..., gt=0),
    data: DishUpdate = Body(...),
):
    dish = crud_dish.update_dish_by_id(dish_id, data.price)
    if not dish:
        raise HTTPException(status_code=404, detail="菜品不存在")
    return {"msg": "修改菜品成功", "data": dish}

@app.delete("/dish/{dish_id}")
def soft_delete_dish_api(dish_id: int = Path(..., gt=0)):
    """软删除：把菜品移入回收站"""
    success = crud_dish.soft_delete_dish(dish_id)
    if not success:
        raise HTTPException(status_code=404, detail="菜品不存在或已删除")
    return {
        "msg": "菜品已移入回收站",
        "data": {"id": dish_id}
    }



class DishStatusUpdate(BaseModel):
    status: int = Field(..., ge=0, le=1)  # 只允许 0 或 1

@app.patch("/dish/{dish_id}/status")
def update_dish_status_api(dish_id: int = Path(..., gt=0), data: DishStatusUpdate = Body(...)):
    print(f"\n[PATCH] ====== 开始处理 ======")
    print(f"[PATCH] dish_id={dish_id}, data={data}")
    
    dish = crud_dish.get_dish_by_id(dish_id)
    print(f"[PATCH] 更新前 dish: {dish}")
    
    if not dish:
        raise HTTPException(status_code=404, detail="菜品不存在或已删除")
    
    if dish['status'] == data.status:
        raise HTTPException(status_code=400, detail="菜品已经是该状态")
    
    success = crud_dish.update_dish_status(dish_id, data.status)
    print(f"[PATCH] update_dish_status 返回: {success}")
    
    if not success:
        raise HTTPException(status_code=404, detail="菜品不存在或已删除")
    
    dish = crud_dish.get_dish_by_id(dish_id)
    print(f"[PATCH] 更新后 dish: {dish}")
    
    return {"msg": "上架成功" if data.status == 1 else "下架成功", "data": dish}

@app.delete("/dish/{dish_id}/hard")
def hard_delete_dish_api(dish_id: int = Path(..., gt=0)):
    """硬删除：彻底从数据库抹除（仅测试/管理后台用）"""
    # TODO: Part 7 完成后，这里必须加订单关联检查
    # if crud_dish.has_orders(dish_id):
    #     raise HTTPException(status_code=400, detail="该菜品已有订单，不能硬删除")
    
    success = crud_dish.hard_delete_dish(dish_id)
    if not success:
        raise HTTPException(status_code=404, detail="菜品不存在")
    return {
        "msg": "菜品已彻底销毁",
        "data": {"id": dish_id}
    }

'''购物车模块接口'''
'''pydantic模型'''
from app.models import CartItemCreate, CartQuantityUpdate
from app.crud import crud_cart

@app.post("/cart/items")  
def add_to_cart_api(req: CartItemCreate, current_user = Depends(get_current_customer)):
    cart_id  = crud_cart.add_to_cart(current_user["user_id"],req.dish_id, req.quantity)
    
    
    if cart_id is None:
        raise HTTPException(status_code=404, detail="菜品不存在、已下架或已删除")
    return {
        "msg": "加入购物车成功",
        "data": {"cart_id": cart_id}
    }

@app.get("/cart")
def get_cart_items_api(current_user = Depends(get_current_customer)):
    items = crud_cart.get_cart_items(current_user["user_id"])
    return {
        "msg": "获取购物车成功",
        "data": items
    }       


@app.put("/cart/items/{cart_id}") 
def update_cart_quantity_api(cart_id: int = Path(..., gt=0), data: CartQuantityUpdate = Body(...),current_user = Depends(get_current_customer)):
    success = crud_cart.update_cart_quantity(current_user["user_id"],cart_id, data.quantity)
    if not success:
        raise HTTPException(status_code=404, detail="购物车项不存在或数量无效")
    return {
        "msg": "修改购物车数量成功",
        "data": {"cart_id": cart_id, "new_quantity": data.quantity}
    }       


@app.delete("/cart/items/{cart_id}") 
def delete_cart_item_api(cart_id: int = Path(..., gt=0), current_user = Depends(get_current_customer)):   
    success = crud_cart.delete_cart_item(current_user["user_id"],cart_id)
    if not success:
        raise HTTPException(status_code=404, detail="购物车项不存在")
    return {
        "msg": "删除购物车项成功",
        "data": {"cart_id": cart_id}
    }

from app.crud import crud_order


# ==================== 订单（Part 7） ====================

@app.post("/orders")
def create_order_api(current_user = Depends(get_current_customer)):
    """提交订单（从购物车）"""
    order_id = crud_order.create_order_from_cart(current_user["user_id"])
    if order_id is None:
        raise HTTPException(status_code=400, detail="购物车为空或菜品不能下单")
    return {
        "msg": "下单成功",
        "data": {"order_id": order_id}   # ← 单个订单号
    }


@app.get("/orders")
def get_orders_api(current_user = Depends(get_current_customer)):
    """查看订单列表"""
    orders = crud_order.get_orders(current_user["user_id"])
    return {"msg": "获取成功", "data": orders}


@app.get("/orders/{order_id}")
def get_order_by_id_api(order_id: int = Path(..., gt=0), current_user = Depends(get_current_customer)):
    """查看订单详情"""
    order = crud_order.get_order_by_id(order_id, current_user["user_id"])
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    return {"msg": "获取成功", "data": order}


from app.crud import crud_payment


# ==================== 支付 ====================

@app.post("/orders/{order_id}/pay")
def pay_order_api(
    order_id: int = Path(..., gt=0),
    current_user = Depends(get_current_customer)
):
    """支付订单（模拟支付）"""
    payment_id, error = crud_payment.pay_order(order_id,current_user["user_id"])
    if error:
        raise HTTPException(status_code=400, detail=error)
    return {
        "msg": "支付成功",
        "data": {"payment_id": payment_id, "order_id": order_id}
    }


@app.get("/payments/{payment_id}")
def get_payment_api(
    payment_id: int = Path(..., gt=0),
    current_user = Depends(get_current_customer)
):
    """查看支付记录详情"""
    payment = crud_payment.get_payment_by_id(payment_id, current_user["user_id"])
    if not payment:
        raise HTTPException(status_code=404, detail="支付记录不存在")
    return {"msg": "获取成功", "data": payment}


@app.get("/orders/{order_id}/payments")
def get_payments_by_order_api(
    order_id: int = Path(..., gt=0),
    current_user = Depends(get_current_customer)
):
    """查看某个订单的所有支付记录"""
    payments = crud_payment.get_payments_by_order(order_id, current_user["user_id"])
    return {"msg": "获取成功", "data": payments}


from app.crud import crud_order_status


# ==================== 订单状态流转（Part 9） ====================

@app.post("/orders/{order_id}/cancel")
def cancel_order_api(order_id: int = Path(..., gt=0), current_user = Depends(get_current_customer)):
    """取消订单（待支付 → 已取消）"""
    result, error = crud_order_status.cancel_order(current_user["user_id"],order_id)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return {
        "msg": "取消成功",
        "data": {"order_id": order_id}
    }
#result, error = ...：接收两个返回值（(结果, 错误信息)

@app.post("/orders/{order_id}/accept")
def accept_order_api(order_id: int = Path(..., gt=0), current_user = Depends(get_current_merchant)):
    """商户接单（已支付 → 已接单）"""
    result, error = crud_order_status.accept_order(current_user["user_id"],order_id)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return {
        "msg": "接单成功",
        "data": {"order_id": order_id}
    }


@app.post("/orders/{order_id}/complete")
def complete_order_api(order_id: int = Path(..., gt=0), current_user = Depends(get_current_merchant)):
    """完成订单（已接单 → 已完成）"""
    result, error = crud_order_status.complete_order(current_user["user_id"],order_id)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return {
        "msg": "订单完成",
        "data": {"order_id": order_id}
    }


@app.post("/orders/{order_id}/refund")
def refund_order_api(order_id: int = Path(..., gt=0), current_user = Depends(get_current_customer)):
    """退款（已支付 → 已退款）"""
    result, error = crud_order_status.refund_order(current_user["user_id"],order_id)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return {
        "msg": "退款成功",
        "data": {"order_id": order_id}
    }



from app.models import UserCreate, UserLogin
from app.crud import crud_user


# ==================== 用户（Part 11.1） ====================
from app.auth import verify_password, create_jwt


@app.post("/register")
def register(req: UserCreate):
    """用户注册"""
    # 1. 检查用户名是否存在
    existing = crud_user.get_user_by_username(req.username)
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")

    # 2. 创建用户
    user_id = crud_user.create_user(req.username, req.password, req.role)

    # 3. 返回
    return {
        "msg": "注册成功",
        "data": {
            "user_id": user_id,
            "username": req.username,
            "role": req.role
        }
    }


@app.post("/login")
def login(req: UserLogin):
    """用户登录"""
    # 1. 查用户
    user = crud_user.get_user_by_username(req.username)

    # 2. 比对密码
    if not user or not verify_password(req.password, user["password"]):
        raise HTTPException(status_code=401, detail="用户名或密码错误")

        # 3. 生成 JWT
    token = create_jwt(user["id"], user["role"])
    
    # 3. 返回（Part 11.2 会返回 token）
    return {
        "msg": "登录成功",
        "data": {
            "token": token,
            "user_id": user["id"],
            "username": user["username"],
            "role": user["role"]
        }
    }

