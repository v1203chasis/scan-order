from selenium.webdriver.common.by import By
from pages.base_page import BasePage


class PaySuccessPage(BasePage):
    """支付成功页"""

    URL = "/pay/confirm"
    SUCCESS_MSG = (By.ID, "pay-success")

    def is_current_page(self):
        return "/pay/confirm" in self.get_current_url()

    def get_success_text(self):
        return self.get_text(self.SUCCESS_MSG)