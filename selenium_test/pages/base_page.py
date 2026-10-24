# pages/base_page.py
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


class BasePage:
    """所有页面类的基类，封装通用能力"""

    def __init__(self, driver, base_url="http://localhost:5000"):
        self.driver = driver
        self.base_url = base_url
        self.wait = WebDriverWait(driver, 10)

    # ========== 打开页面 ==========
    def open(self, path=""):
        self.driver.get(self.base_url + path)
        return self

    # ========== 查找元素 ==========
    def find(self, locator):
        """找单个元素（带等待）"""
        return self.wait.until(EC.visibility_of_element_located(locator))

    def find_all(self, locator):
        """找多个元素（返回列表，找不到返回 []）"""
        return self.driver.find_elements(*locator)  #locator = (By.ID, "username")，find_element 需要的是两个参数（selenium的api模块强制规定）但是我定义的定位是一个元组（BY.di,"query"）,直接输入会被当成一个元素然后会报错，所以就是要用*来拆开这个元组

    # ========== 操作元素 ==========
    def click(self, locator):
        """点击（带等待）"""
        el = self.wait.until(EC.element_to_be_clickable(locator))
        el.click()
        return self#返回当前对象自己（返回操作完的自己）

    def input_text(self, locator, text):
        """输入文本"""
        el = self.wait.until(EC.element_to_be_clickable(locator))
        el.clear()#清空输入框已有的内容
        el.send_keys(text)
        return self

    def get_text(self, locator):
        """获取文本"""
        return self.find(locator).text

    # ========== 页面状态 ==========
    def get_title(self):
        return self.driver.title

    def get_current_url(self):
        return self.driver.current_url#是driver对象的一个属性

    def is_element_visible(self, locator, timeout=3):
        """元素是否可见（不抛异常）"""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(locator)
            )
            return True
        except TimeoutException:#超时之后程序不会一层层往上报错然后导致所有程序奔溃，在抛出异常的时候会被except捕获，进入except分支然后返回false
            return False

    # ========== 等待 ==========
    def wait_url_contains(self, keyword, timeout=10):
        WebDriverWait(self.driver, timeout).until(
            EC.url_contains(keyword)
        )
        return self#等待页面跳转（等待url的变化）

    # ========== 辅助 ==========
    def screenshot(self, name):
        self.driver.save_screenshot(f"{name}.png")
        return self

    # ========== 断言 ==========
    def assert_text(self, locator, expected):
        actual = self.get_text(locator)
        assert actual == expected, f"期望 '{expected}'，实际 '{actual}'"

    def assert_url_contains(self, keyword):
        assert keyword in self.get_current_url(), \
            f"URL 应包含 '{keyword}'，实际 '{self.get_current_url()}'"

    # ========== 子类必须实现 ==========
    def is_current_page(self):
        """判断当前是否在此页面，子类必须实现"""
        raise NotImplementedError("子类必须实现 is_current_page()")