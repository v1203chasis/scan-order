import pytest
from pages.login_page import LoginPage
from pages.menu_page import MenuPage
from pages.cart_page import CartPage

@pytest.fixture
def cart_with_dish(driver, base_url):
    """已登录，且购物车里有黄焖鸡"""
    login = LoginPage(driver, base_url).open()
    menu = login.login("user", "123456")
    driver.get(f"{base_url}/menu")#因为上一步，这个浏览器页面是停留在这个购物车页面的，所以就是要跳转回这个菜单页面，只有页面没有操作的能力
    menu = MenuPage(driver, base_url)#创建一个菜单页对象，这样就可以操控这个页面了
    menu.add_dish_to_cart("黄焖鸡")
    return menu.go_to_cart()#查看购物车

@pytest.fixture
def empty_cart(driver, base_url):
    """已登录，购物车为空"""
    login = LoginPage(driver, base_url).open()
    login.login("user", "123456")
    driver.get(f"{base_url}/cart/clear")
    driver.get(f"{base_url}/cart")
    return CartPage(driver, base_url)

def test_cart_url_and_title(driver, cart_with_dish):
    assert "/cart" in driver.current_url
    assert "购物车" in driver.title
    assert cart_with_dish.is_current_page()#验证是有菜品的购物车

def test_cart_shows_dish(cart_with_dish):
    names = cart_with_dish.get_cart_dish_names()
    assert "黄焖鸡" in names, f"实际：{names}"

def test_cart_total_price(cart_with_dish):
    total_text = cart_with_dish.get_total()
    assert "20" in total_text, f"实际：{total_text}"

def test_cart_empty(empty_cart):
    assert empty_cart.is_empty(), "空购物车应显示提示"


def test_go_back_to_menu(cart_with_dish):
    from selenium.webdriver.common.by import By
    cart_with_dish.click((By.LINK_TEXT, "返回菜单"))
    assert "/menu" in cart_with_dish.get_current_url()


def test_go_to_pay(cart_with_dish):
    """UI_TS_cart_006：点击去支付跳转支付页"""
    from selenium.webdriver.common.by import By
    cart_with_dish.click((By.ID, "go-pay"))
    assert "/pay" in cart_with_dish.get_current_url()
