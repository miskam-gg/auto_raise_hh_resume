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
    """Авторизация на hh.ru и запуск бесконечного цикла подъёма резюме."""
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

        # 2) Нажимаем "Войти"
        login_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'a.supernova-button[data-qa="login"]'))
        )
        login_button.click()
        print("[INFO] Открылась панель авторизации")
        random_delay()

        # 3) Нажимаем "Войти" в панели
        panel_login_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//span[contains(text(), "Войти")]'))
        )
        panel_login_button.click()
        print("[INFO] Кнопка 'Войти' в панели нажата")
        random_delay()

        # 4) Выбираем "Почта"
        email_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//div[contains(text(), "Почта")]'))
        )
        email_button.click()
        print("[INFO] Выбрана опция 'Почта'")
        random_delay()

        # 5) Вводим логин
        username_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[name="username"]'))
        )
        username_input.send_keys(USERNAME)
        print("[INFO] Логин введен")
        random_delay()

        # 6) Нажимаем "Войти с паролем"
        time.sleep(2)
        try:
            password_mode_button = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//span[contains(text(), "Войти с") and contains(text(), "паролем")]'))
            )
            WebDriverWait(driver, 5).until(EC.element_to_be_clickable(password_mode_button))
            password_mode_button.click()
            print("[INFO] Кнопка 'Войти с паролем' нажата.")
            random_delay()
        except:
            print("[ERROR] Не найдена кнопка 'Войти с паролем'. Проверьте структуру страницы.")
            print(driver.page_source)
            raise

        # 7) Вводим пароль
        password_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[name="password"]'))
        )
        password_input.send_keys(PASSWORD)
        print("[INFO] Пароль введен")
        random_delay()

        # 8) Нажимаем "Войти"
        final_login_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((
                By.XPATH, '//span[contains(text(), "Войти")]/ancestor::span[@class="magritte-button__content___BXYU0_5-2-15"]'
            ))
        )
        final_login_button.click()
        print("[INFO] Авторизация завершена!")
        random_delay()

        # 9) Запускаем бесконечный цикл подъёмов
        infinite_raise_cycle(driver)

    except Exception as e:
        print("[ERROR] Произошла ошибка:", e)
        # Если что-то пошло не так, можно закрыть браузер
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

            # 1) Ищем кнопку "Поднять в поиске"
            raise_buttons = driver.find_elements(By.XPATH, "//span[normalize-space()='Поднять в поиске']")

            if raise_buttons:
                # Кнопка доступна прямо сейчас — жмём!
                raise_buttons[0].click()
                print("[INFO] Нажата кнопка 'Поднять в поиске'")
                random_delay()
            
            # 2) Независимо от того, нажата кнопка или нет — ищем, когда следующий раз
            #    (Если кнопка была нажата, HH обычно сразу показывает "Поднять вручную можно сегодня/завтра в ...")
            next_raise_element = None
            try:
                # Элемент вида: <div>Поднять вручную можно сегодня в 21:15</div>
                next_raise_element = driver.find_element(
                    By.XPATH,
                    "//div[contains(text(), 'Поднять вручную можно')]"
                )
            except:
                pass

            if next_raise_element:
                full_text = next_raise_element.text
                print(f"[INFO] Информация о следующем подъёме: {full_text}")

                # Пробуем вытащить (сегодня|завтра) и время HH:MM
                # Примеры:
                #   "Поднять вручную можно сегодня в 21:15"
                #   "Поднять вручную можно завтра в 09:30"
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
                        # Если wait_seconds <= 0, значит время уже прошло
                        # Либо HH показывает что-то некорректное, либо "сегодня в 21:15", а у нас уже 21:20
                        # Попробуем поднять сразу или просто подождём немного
                        print("[WARNING] Похоже, время уже наступило или прошло. Пробуем ещё раз через 5 минут.")
                        time.sleep(5 * 60)
                else:
                    # Не нашли нужный паттерн — просто ждём 30 минут
                    print("[WARNING] Не удалось распарсить время (сегодня/завтра). Ждём 30 минут.")
                    time.sleep(1800)
            else:
                # Если мы не нашли ни кнопки, ни текста — возможно, страница другая или HH что-то поменял
                print("[WARNING] Не нашли ни кнопки 'Поднять в поиске', ни информации о времени. Ждём 30 минут.")
                time.sleep(1800)

        except Exception as e:
            # Если что-то непредвиденное — логируем и спим перед повтором
            print("[ERROR] Сбой в бесконечном цикле:", e)
            time.sleep(300)  # Ждём 5 минут и пробуем заново


def calc_wait_time(day_word, hour, minute):
    """
    Считает, сколько секунд осталось до указанного (сегодня/завтра в HH:MM).
    Возвращает количество секунд (int).
    Если время уже прошло, вернёт <= 0.
    """
    now = datetime.datetime.now()

    # Определяем целевую дату/время
    if day_word == 'сегодня':
        target_day = now.date()  # today's date
    else:  # 'завтра'
        target_day = now.date() + datetime.timedelta(days=1)

    # Формируем datetime нужного дня с указанным часом/минутой
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
