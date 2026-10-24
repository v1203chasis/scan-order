# conftest.py
import pytest
import os
from selenium import webdriver
from selenium.webdriver.edge.options import Options


# ========== 环境变量 ==========
BASE_URL = os.getenv("BASE_URL", "http://localhost:5000")
HEADLESS = os.getenv("HEADLESS", "false").lower() == "true"




@pytest.fixture
def driver():
    """每个用例启动一个新浏览器"""
    options = Options()
    
    # 核心逻辑：如果是无头环境，才加这些参数
    if HEADLESS:
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080") # 无头模式最好指定一下窗口大小

    # 如果你想在本地跑的时候，也避免 Edge 自动下载驱动报错，可以加上这句
    # 但因为你本地已经跑通了，可以先不加。

    d = webdriver.Edge(options=options)
    
    # 如果是在本地（有头模式），最大化窗口方便看
    if not HEADLESS:
        d.maximize_window()
        
    yield d
    d.quit() # 用例结束后，关闭浏览器        # 用例结束后，关闭浏览器


# ========== base_url fixture ==========
@pytest.fixture
def base_url():
    return BASE_URL


# ========== 失败自动截图 hook ==========
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """用例失败时，自动截图"""
    outcome = yield
    report = outcome.get_result()
    if report.when == "call" and report.failed:
        driver = item.funcargs.get("driver")
        if driver:
            name = f"failed_{item.name}.png"
            driver.save_screenshot(name)
            print(f"\n[失败截图] {name}")
            print(f"[当前 URL] {driver.current_url}")
            print(f"[当前标题] {driver.title}")


