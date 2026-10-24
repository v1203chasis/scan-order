10.9日改动
与先前的电商项目做了对比，发现环境变量的设置方面还有优化的地方，可以将修改环境变量的命令行改动为输入关键词就可以修改设置的全部环境变量

优点：方便，牵一发而动全身
缺点：一改就要一起改，没办法做到只改某一个

扫码下单系统的原有部分
在config.py设置了Config类，
Config类的功能主要为使用os来读取命令行中的环境变量（SET）
实例化config = Config（）
###
用类不够灵活
就是说类因为是整个类import过来的，这个类就在import过来的那一瞬间就被拍下了快照，所以说就是后续整个会话的操作都是在这个快照下的环境进行，然后函数的话就是没调用一次就实行一次，可以获得最新的值，其实类里面的函数也是流动的，但是因为import时只读一遍，就被拍快照了


然后如何定位到模块呢
from config import config
db_helper

用模块函数接收变量
DB_PATH = config.DB_PATH
在连接数据库的时候填入环境变量
conn = sqlite3.connect(DB_PATH, isolation_level=None)

要修改base_url的话也是这样

而修改后的代码
不使用类来将方法囊括，而是分为一个个专门负责各自环境变量读取工作的函数
这样在import进不同的模块中，一调用就会回到config去执行，获得命令行中最新的环境变量


修改后的代码
首先时config全改为函数

然后就是在conftest中将详细的环境变量书写好
request.config.getoption取得命令行中的相关内容
传给这个env，然后再找到匹配的
传给这个config = env_map[env]

最后    for key, value in config.items():
        os.environ[key] = value
去遍历整个环境变量
直接将环境变量全部修改好

然后在运行db_helper时，from app.config import get_db_path
config  的os.getenv()读取到当前conftest环境中的环境变量
将这个值传给db_helper



UI 自动化踩坑与解决记录

MenuPage 缺 open() 导致 404
现象：

selenium.common.exceptions.TimeoutException
[当前 URL] http://localhost:5000
原因：MenuPage 没有定义自己的 open()，调用时用的是 BasePage 的：

python
def open(self, path=""):
    self.driver.get(self.base_url + path)   # path="" → 访问根路径 "/"
访问根路径 /，Flask 没定义，404。

错误源代码：
def test_add_dish_to_cart(logged_in_menu):
    """UI_TS_menu_005：点击加购，购物车中数量 +1"""
    # 1. 记录加购前数量
    cart_before = logged_in_menu.go_to_cart()
    names_before = cart_before.get_cart_dish_names()
    qty_before = cart_before.get_quantity_of("黄焖鸡") if "黄焖鸡" in names_before else 0

    # 2. 回菜单页，加购一次
    from pages.menu_page import MenuPage
    menu = MenuPage(logged_in_menu.driver, logged_in_menu.base_url)
    menu.open()                    # ← 这里
    menu.add_dish_to_cart("黄焖鸡")

    # 3. 再看购物车
    cart_after = menu.go_to_cart()
    qty_after = cart_after.get_quantity_of("黄焖鸡")

    # 4. 断言：加购后 == 加购前 + 1
    assert qty_after == qty_before + 1, f"期望 {qty_before + 1}，实际 {qty_after}"

原因：
BasePage.open() 是
def open(self, path=""):
    self.driver.get(self.base_url + path)
    return self
调用 menu.open() → path="" → 访问 http://localhost:8000（根路径）→ 404。


解决：给 MenuPage 加自己的 open()：

第二种：
def test_add_dish_to_cart(logged_in_menu):
    """UI_TS_menu_005：点击加购，购物车中数量 +1"""
    # 1. 记录加购前数量
    cart_before = logged_in_menu.go_to_cart()
    names_before = cart_before.get_cart_dish_names()
    qty_before = cart_before.get_quantity_of("黄焖鸡") if "黄焖鸡" in names_before else 0

    # 2. 回菜单页（用 driver.get 直接跳）
    logged_in_menu.driver.get(f"{logged_in_menu.base_url}/menu")

    # 3. 加购一次
    logged_in_menu.add_dish_to_cart("黄焖鸡")

    # 4. 再看购物车
    cart_after = logged_in_menu.go_to_cart()
    qty_after = cart_after.get_quantity_of("黄焖鸡")

    # 5. 断言：+1
    assert qty_after == qty_before + 1, f"期望 {qty_before + 1}，实际 {qty_after}"

