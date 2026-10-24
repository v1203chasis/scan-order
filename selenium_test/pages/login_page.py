# pages/login_page.py
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from pages.base_page import BasePage


class LoginPage(BasePage):
    """登录页"""

    # ========== 页面路径 ==========
    URL = "/login"

    # ========== 元素定位 ==========
    USERNAME = (By.ID, "username")
    PASSWORD = (By.ID, "password")
    LOGIN_BTN = (By.ID, "login-btn")
    ERROR_MSG = (By.CSS_SELECTOR, ".error-message")   # 页内提示
    # ALERT 类型需要 driver.switch_to.alert，不用定位(#这是 Selenium 处理浏览器原生弹窗（alert）的方式。)

    # ========== 打开页面 ==========
    def open(self):
        self.driver.get(self.base_url + self.URL)
        self.wait.until(EC.visibility_of_element_located(self.USERNAME))
        return self
    #为什么明明父类是有open（）的，子类还是需要去定义这个函数呢（因为等待界面不一样，出现的确定内容也不一样，所以就要自己去定义符合这个页面的）

    # ========== 页面身份 ==========
    def is_current_page(self):
        return "/login" in self.get_current_url()

    # ========== 输入 + 点击 ==========
    def fill_and_submit(self, username, password):
        self.input_text(self.USERNAME, username)
        self.input_text(self.PASSWORD, password)
        self.click(self.LOGIN_BTN)
        return self

    # ========== 完整登录（成功） ==========
    def login(self, username, password):
        self.fill_and_submit(username, password)
        self.wait_url_contains("/menu")
        from pages.menu_page import MenuPage
        return MenuPage(self.driver)#MenuPage(self.driver) 就是一个"创建菜单页对象"的动作，同一个管道，换了个视图。
    #登录成功后，返回"菜单页对象"，让调用者可以直接操作菜单页。

    # ========== 获取错误提示 ==========
    def get_error_msg(self):
        """获取页内错误提示文本"""
        el = self.wait.until(EC.visibility_of_element_located(self.ERROR_MSG))
        return el.text

    # ========== 如果错误提示是 alert ==========
    def get_alert_msg(self):
        """获取 alert 弹窗文本"""
        alert = self.wait.until(EC.alert_is_present())
        text = alert.text
        alert.accept()   # 关闭弹窗
        return text