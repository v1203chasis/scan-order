# 🍽️ Scan-Order 扫码点餐系统

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688?logo=fastapi&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-3-003B57?logo=sqlite&logoColor=white)
![Pytest](https://img.shields.io/badge/Pytest-Automation-0A9EDC?logo=pytest&logoColor=white)
![Selenium](https://img.shields.io/badge/Selenium-UI%20Testing-43B02A?logo=selenium&logoColor=white)
![Allure](https://img.shields.io/badge/Report-Allure-orange)

> 一个基于 FastAPI 的模拟线下扫码点餐系统，包含完整的业务逻辑（顾客/商户双角色）、数据库事务处理以及完善的**接口自动化**与 **UI 自动化测试框架**。

## 📖 项目简介

本项目旨在模拟用户在线下用餐时进行**扫码下单**的真实业务场景。系统分为**顾客端**和**商户端**，涵盖了从浏览菜单、加入购物车、下单支付，到商户接单、完成订单的完整业务闭环。

项目不仅包含基于 FastAPI 的后端 RESTful API，还配备了两套高质量的自动化测试体系：
1. **接口自动化测试**：基于 `Pytest + Requests`，采用 Factory 工厂模式管理测试数据，支持多环境切换。
2. **UI 自动化测试**：基于 `Pytest + Selenium`，采用 Page Object (PO) 设计模式，支持无头模式运行。

## ✨ 核心功能

### 👨‍🍳 商户端 (Merchant)
- **菜品管理**：添加菜品、修改价格、上下架菜品。
- **软删除机制**：移除菜品时采用软删除（`is_deleted=1`），保护历史订单数据完整性。
- **订单处理**：查看已支付订单、接单、完成订单。

### 🙋‍♂️ 顾客端 (Customer)
- **浏览菜单**：仅展示已上架且未被删除的菜品。
- **购物车管理**：添加菜品（自动累加）、修改数量、删除菜品。
- **订单操作**：提交订单（事务保证）、模拟支付、取消订单、申请退款。

## 🛠️ 技术栈

- **后端框架**：FastAPI
- **数据库**：SQLite (原生 SQL，包含事务控制、乐观锁防并发)
- **身份认证**：JWT (PyJWT) + Bcrypt (密码加密)
- **接口测试**：Pytest + Requests + YAML 数据驱动
- **UI 测试**：Pytest + Selenium (Page Object 模式)
- **测试报告**：Allure Pytest

## 📂 项目结构

```text
scan-order/
├── app/                    # 核心后端目录
│   ├── crud/               # 数据库 CRUD 操作 (模块化)
│   ├── auth.py             # JWT 与密码哈希工具
│   ├── config.py           # 配置管理 (支持环境变量)
│   ├── db_helper.py        # SQLite 连接与建表
│   ├── dependencies.py     # FastAPI 依赖注入 (权限校验)
│   ├── main.py             # FastAPI 路由入口
│   └── models.py           # Pydantic 数据校验模型
├── tests/                  # 接口自动化测试目录
│   ├── conftest.py         # 核心 Fixtures (环境切换、数据清理、Factory 工厂)
│   ├── test_data/          # YAML 测试数据
│   ├── test_auth.py        # 认证模块测试
│   ├── test_cart.py        # 购物车接口测试
│   ├── test_dish.py        # 菜品管理测试
│   ├── test_order.py       # 订单流转测试
│   └── test_user.py        # 用户注册登录测试
├── selenium_test/          # UI 自动化测试目录
│   ├── pages/              # Page Object 页面对象封装
│   ├── tests/              # UI 测试用例
│   └── conftest.py         # Selenium 驱动初始化与截图 Hook
├── requirements.txt        # 项目依赖
└── README.md



1. 克隆项目并安装依赖
git clone https://github.com/xiaovchasis0613/scan-order.git
cd scan-order

# 创建虚拟环境
python -m venv .venv
# Windows 激活: .venv\Scripts\activate
# Mac/Linux 激活: source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt


2. 启动后端服务
uvicorn app.main:app --reload
启动后，访问 http://127.0.0.1:8000/docs 即可查看 FastAPI 自动生成的 Swagger API 文档。





🧪 自动化测试体系 (核心亮点)
本项目高度重视测试代码的工程化，遵循了测试隔离与数据驱动的最佳实践。

1. 接口自动化测试 (Pytest + Requests)
Factory 工厂模式：通过 dish_factory、cart_factory、order_factory 快速生成测试数据，并在用例结束后自动清理数据库，保证用例相互隔离。

多环境支持：支持通过 --env 参数切换测试环境（如 --env=test 使用测试数据库）。

断言严谨：不仅校验 HTTP 状态码与响应体，还通过注入 db fixture 直接校验数据库落盘状态（如软删除、金额计算、订单快照）。

运行接口测试：

# 默认使用 dev 环境 (scan_order.db)
pytest tests/

# 指定测试环境 (test_scan_order.db)
pytest tests/ --env=test
2. UI 自动化测试 (Selenium)
Page Object (PO) 模式：将页面元素定位与业务操作分离（如 LoginPage、CartPage），降低代码冗余，提升可维护性。

失败自动截图：conftest.py 中注入了 pytest_runtest_makereport Hook，用例失败时自动截图并记录当前 URL，方便排查。

无头模式：支持通过环境变量 HEADLESS=true 在后台静默运行 UI 测试，非常适合 CI/CD 流水线。

运行 UI 测试：


# 确保本地已启动后端服务 (http://localhost:5000)
set HEADLESS=true  # Windows (如果不加，会弹出浏览器)
# export HEADLESS=true # Mac/Linux

pytest selenium_test/
3. 生成 Allure 可视化报告

# 运行测试并收集报告数据
pytest tests/ --alluredir=./allure-results

# 生成并打开 HTML 报告
allure serve ./allure-results
💡 数据库设计与架构亮点
购物车表 (cart_items)：使用联合唯一索引 UNIQUE (user_id, dish_id) 防止重复插入，配合代码逻辑实现商品数量累加。

订单快照：订单项 (order_items) 保存了菜品名称和当时的单价，即使商户后续修改菜品价格或删除菜品，历史订单数据依然准确。

并发控制：在支付、接单、退款等状态流转中，使用 SQL UPDATE ... WHERE status = 'xxx' 实现乐观锁，防止高并发下的重复支付或状态错乱。