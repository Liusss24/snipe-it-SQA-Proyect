import os
import pytest
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from pages.login_page import LoginPage

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

BASE_URL   = os.getenv("SNIPEIT_BASE_URL",        "http://localhost:8000")
ADMIN_USER = os.getenv("SNIPEIT_ADMIN_USERNAME",  "admin")
ADMIN_PASS = os.getenv("SNIPEIT_ADMIN_PASSWORD",  "Contrasena123")


def pytest_addoption(parser):
    parser.addoption("--headless",    action="store_true", default=False)
    parser.addoption("--base-url",    action="store",      default=BASE_URL)
    parser.addoption("--admin-user",  action="store",      default=ADMIN_USER)
    parser.addoption("--admin-pass",  action="store",      default=ADMIN_PASS)


@pytest.fixture(scope="session")
def base_url(request):
    return request.config.getoption("--base-url")


@pytest.fixture(scope="session")
def driver(request):
    options = webdriver.ChromeOptions()
    if request.config.getoption("--headless"):
        options.add_argument("--headless=new")
        options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-extensions")

    service = Service(ChromeDriverManager().install())
    drv = webdriver.Chrome(service=service, options=options)
    drv.implicitly_wait(10)
    drv.maximize_window()
    yield drv
    drv.quit()


@pytest.fixture(scope="session")
def credentials(request):
    return {
        "username": request.config.getoption("--admin-user"),
        "password": request.config.getoption("--admin-pass"),
    }


@pytest.fixture(scope="session")
def logged_in_driver(driver, base_url, credentials):
    login_page = LoginPage(driver, base_url)
    login_page.load()
    login_page.login(credentials["username"], credentials["password"])
    yield driver
