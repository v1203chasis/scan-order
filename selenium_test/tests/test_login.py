import pytest
from pages.login_page import LoginPage   


@pytest.fixture
def test_login_page(driver,base_url):
    login = LoginPage(driver,base_url).open()
    return login
    

def test_login_success(driver, test_login_page):
    """TS_login_001：登录成功跳菜单页"""
    
    menu = test_login_page.login("user", "123456")
    assert "/menu" in driver.current_url, "登录后未跳转"
    assert menu.is_current_page(), "未进入菜单页"


def test_login_wrong_username(driver, base_url):
    """TS_login_002：用户名错误提示"""
    login = LoginPage(driver, base_url).open()
    login.fill_and_submit("wrong", "123456")

    assert "/login" in driver.current_url, "不应该跳转"
    msg = login.get_error_msg()
    assert "用户名或密码错误" in msg, f"实际提示：{msg}"


def test_login_wrong_password(driver, base_url):
    """TS_login_003：密码错误提示"""
    login = LoginPage(driver, base_url).open()
    login.fill_and_submit("user", "wrong")

    assert "/login" in driver.current_url, "不应该跳转"
    msg = login.get_error_msg()
    assert "用户名或密码错误" in msg, f"实际提示：{msg}"


@pytest.mark.parametrize("username, password, expected", [
    ("", "123456", "请输入用户名"),
    ("user", "", "请输入密码"),
])
def test_login_input_validation(driver, base_url, username, password, expected):
    """输入框校验（数据驱动）"""
    login = LoginPage(driver, base_url).open()
    login.fill_and_submit(username, password)
    msg = login.get_error_msg()
    assert expected in msg, f"实际提示：{msg}"