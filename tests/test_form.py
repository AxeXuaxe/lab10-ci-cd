import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

ROOT = Path(__file__).resolve().parents[1]


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        return


@pytest.fixture(scope="session")
def base_url():
    handler = partial(QuietHandler, directory=str(ROOT))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    yield f"http://{host}:{port}/index.html"
    server.shutdown()


@pytest.fixture
def driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1280,900")
    browser = webdriver.Chrome(options=options)
    yield browser
    browser.quit()


def open_page(driver, base_url):
    driver.get(base_url)
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "signup-form")))


def test_page_title_and_heading(driver, base_url):
    open_page(driver, base_url)
    assert driver.title == "Запись на курс"
    heading = driver.find_element(By.ID, "heading")
    assert heading.text == "Запись на курс тестирования"


def test_form_fields_and_button(driver, base_url):
    open_page(driver, base_url)
    assert driver.find_element(By.ID, "name").is_displayed()
    assert driver.find_element(By.ID, "email").is_displayed()
    assert driver.find_element(By.ID, "password").is_displayed()
    button = driver.find_element(By.ID, "submit-btn")
    assert button.text.strip() == "Отправить"
    assert driver.find_element(By.ID, "success").is_displayed() is False


def test_empty_submit_shows_validation_errors(driver, base_url):
    open_page(driver, base_url)
    driver.find_element(By.ID, "submit-btn").click()

    assert "имя" in driver.find_element(By.ID, "name-error").text.lower()
    assert "email" in driver.find_element(By.ID, "email-error").text.lower()
    assert "пароль" in driver.find_element(By.ID, "password-error").text.lower()
    assert driver.find_element(By.ID, "success").is_displayed() is False
    assert driver.find_element(By.ID, "signup-form").is_displayed() is True


def test_valid_submit_shows_success(driver, base_url):
    open_page(driver, base_url)
    driver.find_element(By.ID, "name").send_keys("Анна")
    driver.find_element(By.ID, "email").send_keys("anna@example.com")
    driver.find_element(By.ID, "password").send_keys("secret1")
    driver.find_element(By.ID, "submit-btn").click()

    success = WebDriverWait(driver, 5).until(
        EC.visibility_of_element_located((By.ID, "success"))
    )
    assert "Заявка принята" in success.text
    assert "Анна" in driver.find_element(By.ID, "success-text").text
    assert driver.find_element(By.ID, "signup-form").is_displayed() is False
