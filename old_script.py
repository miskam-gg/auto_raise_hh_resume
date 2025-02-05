#СТАРАЯ АВТОРИЗАЦИЯ, ВЕРНУЛИ ЕЕ 03.02.2025г.
import time
import random
import re
import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv
import os

# Загрузка переменных из .env
load_dotenv()
USERNAME = os.getenv("HH_USERNAME")
PASSWORD = os.getenv("HH_PASSWORD")

def random_delay(minimum=3, maximum=5):
    """Функция для добавления случайной задержки от min до max секунд."""
    delay = random.uniform(minimum, maximum)
    time.sleep(delay)

def open_hh_and_login():
    """
    Авторизация на hh.ru через "старую" авторизацию:
      1) На главной нажимаем кнопку "Войти"
      2) Вводим логин
      3) Нажимаем "Войти с паролем"
      4) Вводим пароль
      5) Нажимаем "Войти в личный кабинет"
    Затем запускаем бесконечный цикл подъёмов.
    """
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    try:
        # 1) Открываем hh.ru
        driver.get("https://hh.ru")
        print("[INFO] Открыта главная страница HH")
        random_delay()

        # 2) Нажимаем "Войти" (селектор по data-qa="login")
        login_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'a.supernova-button[data-qa="login"]'))
        )
        login_button.click()
        print("[INFO] Нажали кнопку 'Войти' на главной странице")
        random_delay()

        # 3) Вводим логин (input[name="login"])
        login_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[name="login"]'))
        )
        login_input.send_keys(USERNAME)
        print("[INFO] Логин введен")
        random_delay()

        # 4) Нажимаем "Войти с паролем" (span[data-qa="expand-login-by-password-text"])
        expand_password_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'span[data-qa="expand-login-by-password-text"]'))
        )
        expand_password_btn.click()
        print("[INFO] Нажата кнопка 'Войти с паролем'")
        random_delay()

        # 5) Вводим пароль (input[data-qa="login-input-password"] или input[name="password"])
        password_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[data-qa="login-input-password"]'))
        )
        password_input.send_keys(PASSWORD)
        print("[INFO] Пароль введен")
        random_delay()

        # 6) Нажимаем "Войти в личный кабинет" (текст в кнопке)
        #    Здесь используем XPATH по тексту (или CSS, если есть хороший data-qa).
        final_login_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//span[contains(text(), "Войти в личный кабинет")]'))
        )
        final_login_button.click()
        print("[INFO] Нажата кнопка 'Войти в личный кабинет'")
        random_delay()

        print("[INFO] Авторизация завершена!")
        
        # Запускаем бесконечный цикл подъёмов резюме
        infinite_raise_cycle(driver)

    except Exception as e:
        print("[ERROR] Произошла ошибка при авторизации:", e)
        driver.quit()


def infinite_raise_cycle(driver):
    """
    Бесконечный цикл:
      1) Переходим на страницу "Мои резюме"
      2) Ищем кнопку "Поднять в поиске"
         - Если есть, жмём и логируем
         - Если нет, ищем текст "Поднять вручную можно сегодня/завтра в 21:15"
      3) Парсим время, ждём до этого момента
      4) Повторяем
    """
    while True:
        try:
            # Переходим в "Мои резюме"
            driver.get("https://hh.ru/applicant/resumes")
            print("[INFO] Открыли страницу 'Мои резюме'")
            random_delay()

            # Ищем кнопку "Поднять в поиске"
            raise_buttons = driver.find_elements(By.XPATH, "//span[normalize-space()='Поднять в поиске']")

            if raise_buttons:
                # Кнопка доступна прямо сейчас — жмём!
                raise_buttons[0].click()
                print("[INFO] Нажата кнопка 'Поднять в поиске'")
                random_delay()
            
            # Независимо от того, нажали кнопку или нет — ищем информацию о следующем подъёме
            next_raise_element = None
            try:
                # Примерный локатор для блока: "Поднять вручную можно сегодня в 21:15"
                next_raise_element = driver.find_element(
                    By.XPATH,
                    "//div[contains(text(), 'Поднять вручную можно')]"
                )
            except:
                pass

            if next_raise_element:
                full_text = next_raise_element.text
                print(f"[INFO] Информация о следующем подъёме: {full_text}")

                # Ищем (сегодня|завтра) и время HH:MM
                match = re.search(r"(сегодня|завтра)\s*в\s*(\d{1,2}):(\d{1,2})", full_text)
                if match:
                    day_word = match.group(1)      # "сегодня" или "завтра"
                    hour = int(match.group(2))
                    minute = int(match.group(3))

                    wait_seconds = calc_wait_time(day_word, hour, minute)
                    if wait_seconds > 0:
                        print(f"[INFO] Ждём {wait_seconds} секунд до следующего подъёма ({day_word} в {hour:02d}:{minute:02d}).")
                        time.sleep(wait_seconds)
                    else:
                        print("[WARNING] Время уже наступило или прошло. Подождём 5 минут и попробуем ещё раз.")
                        time.sleep(5 * 60)
                else:
                    print("[WARNING] Не удалось распарсить время (сегодня/завтра). Ждём 30 минут.")
                    time.sleep(1800)
            else:
                print("[WARNING] Не нашли ни кнопки 'Поднять в поиске', ни информации о времени. Ждём 30 минут.")
                time.sleep(1800)

        except Exception as e:
            print("[ERROR] Сбой в бесконечном цикле:", e)
            time.sleep(300)  # Ждём 5 минут и пробуем заново


def calc_wait_time(day_word, hour, minute):
    """
    Считает, сколько секунд осталось до указанного (сегодня/завтра в HH:MM).
    Возвращает количество секунд (int).
    Если время уже прошло, вернёт <= 0.
    """
    now = datetime.datetime.now()

    if day_word == 'сегодня':
        target_day = now.date()
    else:  # 'завтра'
        target_day = now.date() + datetime.timedelta(days=1)

    target_dt = datetime.datetime(
        year=now.year,
        month=now.month,
        day=target_day.day,
        hour=hour,
        minute=minute,
        second=0,
        microsecond=0
    )

    delta = target_dt - now
    return int(delta.total_seconds())


if __name__ == "__main__":
    open_hh_and_login()
