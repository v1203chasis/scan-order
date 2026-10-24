# pages/menu_page.py
from selenium.webdriver.common.by import By
from pages.base_page import BasePage


class MenuPage(BasePage):
    URL = "/menu"
    WELCOME = (By.ID, "welcome")
    DISH_ITEMS = (By.CSS_SELECTOR, ".dish-item")
    GO_CART = (By.ID, "go-cart")

    def is_current_page(self):
        return "/menu" in self.get_current_url()

    def get_welcome_text(self):
        return self.get_text(self.WELCOME)

    def get_dish_names(self):
        items = self.find_all(self.DISH_ITEMS)#利用样式解释器的方法去定位这个菜品名然后获得网页中的元素列表
        return [el.get_attribute("data-dish-name") for el in items]
#遍历items，el是每一个元素对象，get_attribute()是元素对象的方法，输入值是属性名字，返回值是这个属性的值
#如果属性不存在，返回none
#data-dish-name="黄焖鸡"是前端定义的

    # ↓↓↓ 新增 ↓↓↓
    def get_dish_count(self):
        return len(self.find_all(self.DISH_ITEMS))

    def add_dish_to_cart(self, dish_name):
        xpath = f"//div[@data-dish-name='{dish_name}']//a[contains(@class, 'add-btn')]"
        self.click((By.XPATH, xpath))
        return self
    
    def add_dish_to_cart(self, dish_name):
        """点击某道菜的加购按钮"""
        xpath = f"//div[@data-dish-name='{dish_name}']//a[contains(@class, 'add-btn')]"
        self.click((By.XPATH, xpath))
        return self

    def go_to_cart(self):
        self.click(self.GO_CART)
        from pages.cart_page import CartPage
        return CartPage(self.driver)
    #为什么到跳转到另外一个页面的时候都是要返回一个这个跳转到的目标页面的对象呢？
    #操作页面必须通过该页面的对象，返回目标页面对象后就可以对这个对象进行操作了
    #例如我要知道我跳转的页面是否正确，就要使用到这个页面的is_current_page这个函数
