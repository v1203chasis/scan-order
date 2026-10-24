from selenium import webdriver


def test_open_baidu():
    d = webdriver.Edge()
    d.get("https://www.baidu.com")
    print("标题:", d.title)
    d.quit()