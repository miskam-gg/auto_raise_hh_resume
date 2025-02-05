import time
import random
import re
import datetime
import os
import logging

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv

# Настройка логирования (подробный вывод)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Загрузка переменных из .env
load_dotenv()
USERNAME = os.getenv("HH_USERNAME")
PASSWORD = os.getenv("HH_PASSWORD")

def random_delay(minimum=3, maximum=5):
    """Вставляет случайную задержку для имитации поведения пользователя."""
    delay = random.uniform(minimum, maximum)
    logging.debug(f"Задержка {delay:.2f} секунд")
    time.sleep(delay)

def open_hh_and_login():
    options = Options()
    
    # Общие опции для стабильной работы
    options.add_argument("--start-maximized")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--allow-running-insecure-content")
    options.add_argument("--disable-web-security")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    
    # Дополнительные опции для обхода защиты автоматизации и устранения ошибок SSL/WebGL
    options.add_argument("--disable-quic")
    options.add_argument("--enable-unsafe-swiftshader")  # Включаем SwiftShader (предупреждения SSL/WebGL)
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/113.0.0.0 Safari/537.36"
    )
    
    # Включаем логирование браузера и установку небезопасных сертификатов
    options.set_capability("goog:loggingPrefs", {"browser": "ALL", "driver": "ALL", "performance": "ALL"})
    options.set_capability("acceptInsecureCerts", True)
    
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    
    # Отключаем navigator.webdriver для сокрытия факта автоматизации
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })

    try:
        # Переходим на страницу логина с параметром backurl, чтобы после авторизации попасть в личный кабинет
        login_url = "https://hh.ru/account/login?backurl=%2Fapplicant%2Fresumes"
        logging.info("Открываем страницу логина: " + login_url)
        driver.get(login_url)
        random_delay()

        logging.info("Нажимаем кнопку 'Войти'")
        login_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'a.supernova-button[data-qa="login"]'))
        )
        login_button.click()
        logging.info("Нажата кнопка 'Войти'")
        random_delay()

        logging.info("Вводим логин")
        login_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[name="login"]'))
        )
        login_input.send_keys(USERNAME)
        logging.info("Логин введён")
        random_delay()

        logging.info("Нажимаем кнопку 'Войти с паролем'")
        expand_pass_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'span[data-qa="expand-login-by-password-text"]'))
        )
        expand_pass_btn.click()
        logging.info("Нажата кнопка 'Войти с паролем'")
        random_delay()

        logging.info("Вводим пароль")
        password_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[data-qa="login-input-password"]'))
        )
        password_input.send_keys(PASSWORD)
        logging.info("Пароль введён")
        random_delay()

        # Нажимаем кнопку "Войти в личный кабинет"
        logging.info("Ожидание кнопки 'Войти в личный кабинет'")
        # Здесь используем XPath с поиском по подстрокам "Войти" и "личный"
        final_login_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//*[contains(., 'Войти') and contains(., 'личный')]"))
        )
        logging.debug("Найдена кнопка 'Войти в личный кабинет', outerHTML: " + final_login_button.get_attribute('outerHTML'))
        final_login_button.click()
        logging.info("Клик по кнопке 'Войти в личный кабинет'")
        random_delay()

        # Ждем редиректа и проверяем URL
        time.sleep(5)
        current_url = driver.current_url
        logging.info("Текущий URL после входа: " + current_url)
        if "applicant" not in current_url:
            logging.info("URL не содержит 'applicant', выполняем принудительный переход на страницу резюме")
            forced_url = "https://vladimir.hh.ru/applicant/resumes"  # При необходимости замените домен
            driver.get(forced_url)
            time.sleep(5)
            logging.info("Новый URL: " + driver.current_url)
        
        logging.info("Авторизация завершена!")
        infinite_raise_cycle(driver)

    except Exception as e:
        logging.exception("Ошибка при авторизации:")
        try:
            browser_logs = driver.get_log('browser')
            logging.error("Логи браузера:")
            for entry in browser_logs:
                logging.error(entry)
        except Exception as log_exception:
            logging.error("Ошибка при получении логов браузера: " + str(log_exception))
        driver.quit()

def infinite_raise_cycle(driver):
    """
    Бесконечный цикл подъёма резюме:
      1) Переход на страницу "Мои резюме"
      2) Поиск и клик по кнопке "Поднять в поиске" (если доступна)
      3) Поиск информации о следующем подъёме и ожидание нужного времени
    """
    while True:
        try:
            driver.get("https://hh.ru/applicant/resumes")
            logging.info("Открыли страницу 'Мои резюме'")
            random_delay()

            raise_buttons = driver.find_elements(By.XPATH, "//span[normalize-space()='Поднять в поиске']")
            if raise_buttons:
                driver.execute_script("arguments[0].click();", raise_buttons[0])
                logging.info("Нажата кнопка 'Поднять в поиске'")
                random_delay()

            # Поиск информации о следующем подъёме
            next_raise_element = None
            try:
                next_raise_element = driver.find_element(
                    By.XPATH,
                    "//div[contains(text(), 'Поднять вручную можно')]"
                )
            except Exception as inner_e:
                logging.warning("Информация о следующем подъёме не найдена: " + str(inner_e))

            if next_raise_element:
                full_text = next_raise_element.text
                logging.info(f"Информация о следующем подъёме: {full_text}")
                match = re.search(r"(сегодня|завтра)\s*в\s*(\d{1,2}):(\d{1,2})", full_text)
                if match:
                    day_word = match.group(1)
                    hour = int(match.group(2))
                    minute = int(match.group(3))
                    wait_seconds = calc_wait_time(day_word, hour, minute)
                    if wait_seconds > 0:
                        logging.info(f"Ждем {wait_seconds} секунд до следующего подъёма ({day_word} в {hour:02d}:{minute:02d}).")
                        time.sleep(wait_seconds)
                    else:
                        logging.warning("Время уже наступило или прошло. Ждем 5 минут.")
                        time.sleep(5 * 60)
                else:
                    logging.warning("Не удалось распарсить время. Ждем 30 минут.")
                    time.sleep(1800)
            else:
                logging.warning("Не нашли ни кнопки 'Поднять в поиске', ни информации о времени. Ждем 30 минут.")
                time.sleep(1800)

        except Exception as e:
            logging.exception("Сбой в бесконечном цикле:")
            time.sleep(300)

def calc_wait_time(day_word, hour, minute):
    """
    Вычисляет, сколько секунд осталось до указанного времени (сегодня/завтра в HH:MM).
    Если время уже прошло, возвращает число, меньшее или равное 0.
    """
    now = datetime.datetime.now()
    target_day = now.date() if day_word.lower() == 'сегодня' else now.date() + datetime.timedelta(days=1)
    target_dt = datetime.datetime(now.year, now.month, target_day.day, hour, minute, 0, 0)
    return int((target_dt - now).total_seconds())

if __name__ == "__main__":
    open_hh_and_login()
