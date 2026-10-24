import pytest
from pages.login_page import LoginPage
from pages.menu_page import MenuPage
from pages.cart_page import CartPage


@pytest.fixture
def pay_page(driver, base_url):
    """已登录，购物车有菜，跳到支付页"""
    login = LoginPage(driver, base_url).open()
    menu = login.login("user", "123456")
    driver.get(f"{base_url}/cart/clear")
    driver.get(f"{base_url}/menu")
    menu = MenuPage(driver, base_url)
    menu.add_dish_to_cart("黄焖鸡")
    cart = menu.go_to_cart()
    return cart.go_to_pay()


def test_pay_page_load(driver, pay_page):
    """UI_TS_pay_001：支付页加载正确"""
    assert "/pay" in driver.current_url, f"实际 URL：{driver.current_url}"
    assert pay_page.is_current_page(), "未进入支付页"


def test_pay_page_welcome(pay_page):
    """UI_TS_pay_002：支付页显示用户信息"""
    text = pay_page.get_welcome_text()
    assert "user" in text, f"实际文本：{text}"


def test_confirm_pay_success(driver, pay_page):
    """UI_TS_pay_003：确认支付，跳转支付成功页"""
    success_page = pay_page.confirm_pay()
    assert "/pay/confirm" in driver.current_url, f"实际 URL：{driver.current_url}"
    assert success_page.is_current_page(), "未进入支付成功页"
    assert "支付成功" in success_page.get_success_text(), "支付成功文本未出现"