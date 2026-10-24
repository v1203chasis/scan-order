# mock_app/app.py
from flask import Flask, render_template, request, redirect, url_for, session, jsonify

app = Flask(__name__)
app.secret_key = "secret-key-for-test"

# ========== 假数据 ==========
USERS = {
    "user": "123456",
    "admin": "admin123",
}

DISHES = [
    {"id": 1, "name": "黄焖鸡", "price": 20.0},
    {"id": 2, "name": "可乐",   "price": 3.0},
    {"id": 3, "name": "米饭",   "price": 2.0},
]

# 内存购物车：{username: {dish_id: quantity}}
CARTS = {}


# ========== 登录 ==========
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html", error=None)

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    if not username:
        return render_template("login.html", error="请输入用户名")
    if not password:
        return render_template("login.html", error="请输入密码")
    if username not in USERS or USERS[username] != password:
        return render_template("login.html", error="用户名或密码错误")

    session["user"] = username
    CARTS[username] = {}   # ← 加这一行
    return redirect(url_for("menu"))


# ========== 菜单页 ==========
@app.route("/menu")
def menu():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("menu.html", user=session["user"], dishes=DISHES)


# ========== 加购物车 ==========
@app.route("/cart/add/<int:dish_id>")
def cart_add(dish_id):
    if "user" not in session:
        return redirect(url_for("login"))
    user = session["user"]
    cart = CARTS.setdefault(user, {})
    cart[dish_id] = cart.get(dish_id, 0) + 1
    return redirect(url_for("menu"))


# ========== 购物车页 ==========
@app.route("/cart")
def cart():
    if "user" not in session:
        return redirect(url_for("login"))
    user = session["user"]
    cart = CARTS.get(user, {})
    items = []
    total = 0
    for dish in DISHES:
        if dish["id"] in cart:
            qty = cart[dish["id"]]
            subtotal = dish["price"] * qty
            items.append({"name": dish["name"], "price": dish["price"], "qty": qty, "subtotal": subtotal})
            total += subtotal
    return render_template("cart.html", user=user, items=items, total=total)


# ========== 清空 ==========

@app.route("/cart/clear")
def cart_clear():
    if "user" in session:
        CARTS[session["user"]] = {}
    return redirect(url_for("menu"))

# ========== 退出 ==========
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

@app.route("/pay")
def pay():
    if "user" not in session:
        return redirect(url_for("login"))
    user = session["user"]
    cart = CARTS.get(user, {})
    if not cart:
        # 购物车为空，不能支付
        return redirect(url_for("cart"))
    # 简单展示：支付页
    return render_template("pay.html", user=user)


@app.route("/pay/confirm")
def pay_confirm():
    if "user" not in session:
        return redirect(url_for("login"))
    user = session["user"]
    # 清空购物车（模拟支付成功）
    CARTS[user] = {}
    return render_template("pay_success.html", user=user)



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)