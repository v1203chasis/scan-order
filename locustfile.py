from locust import HttpUser, task, between
import random
#HttpUser用户基类
class DishUser(HttpUser):
    wait_time = between(0.5, 1.5) 
    """模拟点餐用户"""

    host = "http://127.0.0.1:8000"#被测地址，对应base_url

    # wait_time请求间隔 每个请求之间，等 1-3 秒

    @task(3)                        # 权重 1，较少执行
    def get_menu(self):
        """压测查询菜品接口"""
        self.client.get("/dish/1")

    @task(1)
    def create_dish(self):
        name = f"压测菜_{random.randint(1, 10000000)}"
        self.client.post("/dish", json={"name": name, "price": 9.9})