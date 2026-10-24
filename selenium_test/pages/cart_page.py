# pages/cart_page.py
from selenium.webdriver.common.by import By
from pages.base_page import BasePage


class CartPage(BasePage):
    URL = "/cart"
    CART_ITEMS = (By.CSS_SELECTOR, ".cart-item")#.class值
    TOTAL = (By.ID, "total")
    EMPTY_MSG = (By.ID, "empty-msg")

    def is_current_page(self):
        return "/cart" in self.get_current_url()

    def get_cart_dish_names(self):
        items = self.find_all(self.CART_ITEMS)
        return [el.get_attribute("data-dish-name") for el in items]

    def get_total(self):
        return self.get_text(self.TOTAL)

    def is_empty(self):
        return self.is_element_visible(self.EMPTY_MSG, timeout=2)

    def get_quantity_of(self, dish_name):
        """获取某道菜的数量"""
        items = self.find_all(self.CART_ITEMS)
        for el in items:
            if el.get_attribute("data-dish-name") == dish_name:
                # 从文本里解析 "黄焖鸡 x 1 = ￥20.0"
                text = el.text
                # 用正则提取数量
                import re
                match = re.search(r"x\s*(\d+)", text)
                if match:
                    return int(match.group(1))
        return 0 


    def go_to_pay(self):
        """点击去支付，跳转支付页"""
        from selenium.webdriver.common.by import By
        self.click((By.ID, "go-pay"))
        self.wait_url_contains("/pay")
        from pages.pay_page import PayPage
        return PayPage(self.driver)