# selenium_test/tests/test_menu.py
import pytest
from pages.login_page import LoginPage


@pytest.fixture
def logged_in_menu(driver, base_url):
    """已登录的菜单页 fixture"""
    login = LoginPage(driver, base_url).open()
    menu = login.login("user", "123456")
    return menu


def test_menu_url_and_title(driver, base_url, logged_in_menu):
    """UI_TS_menu_001：URL 和标题正确"""
    assert "/menu" in driver.current_url, f"实际 URL：{driver.current_url}"
    assert "菜单" in driver.title, f"实际标题：{driver.title}"
    assert logged_in_menu.is_current_page(), "未进入菜单页"


def test_menu_welcome_text(logged_in_menu):
    """UI_TS_menu_002：欢迎语显示"""
    text = logged_in_menu.get_welcome_text()
    assert "欢迎" in text, f"实际文本：{text}"
    assert "user" in text, f"实际文本：{text}"


def test_menu_dish_count(logged_in_menu):
    """UI_TS_menu_003：菜品数量正确"""
    count = logged_in_menu.get_dish_count()
    assert count == 3, f"实际数量：{count}，期望 3"


def test_menu_dish_names(logged_in_menu):
    """UI_TS_menu_004：代表菜品出现"""
    names = logged_in_menu.get_dish_names()
    assert "黄焖鸡" in names, f"实际菜品：{names}"
    assert "可乐" in names, f"实际菜品：{names}"
    assert "米饭" in names, f"实际菜品：{names}"


def test_menu_requires_login(driver, base_url):
    """UI_TS_menu_007：未登录访问菜单页，跳回登录页"""
    # 直接访问 /menu（此时没有登录 session）
    driver.get(f"{base_url}/menu")

    # 等重定向完成（URL 变成 /login）
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    WebDriverWait(driver, 10).until(EC.url_contains("/login"))

    # 断言 1：URL 被重定向到 /login
    assert "/login" in driver.current_url, f"实际 URL：{driver.current_url}"

    # 断言 2：登录页元素出现
    from pages.login_page import LoginPage
    login = LoginPage(driver, base_url)
    assert login.is_element_visible(login.USERNAME), "登录页用户名输入框未出现"


def test_go_to_cart(logged_in_menu):
    """UI_TS_menu_006：点击查看购物车，跳转正确"""
    cart = logged_in_menu.go_to_cart()

    # 断言 1：URL 变成 /cart
    assert "/cart" in cart.get_current_url(), f"实际 URL：{cart.get_current_url()}"
    # 断言 2：购物车页身份
    assert cart.is_current_page(), "未进入购物车页"

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