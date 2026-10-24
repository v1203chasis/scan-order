from selenium.webdriver.common.by import By
from pages.base_page import BasePage


class PayPage(BasePage):
    """支付页"""

    URL = "/pay"
    WELCOME = (By.ID, "pay-welcome")
    CONFIRM_BTN = (By.ID, "confirm-pay")

    def is_current_page(self):
        return "/pay" in self.get_current_url()

    def get_welcome_text(self):
        return self.get_text(self.WELCOME)

    def confirm_pay(self):
        """点击确认支付，返回支付成功页"""
        self.click(self.CONFIRM_BTN)
        self.wait_url_contains("/pay/confirm")
        from pages.pay_success_page import PaySuccessPage
        return PaySuccessPage(self.driver)