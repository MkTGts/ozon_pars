import json
import time
from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from functions import page_down


def get_products_links(item_name:str="наушники беспроводные"):
    '''Собирает ссылки на товару по запросу, переданному аргументом в функцию
    Для пауз используется стандартный time.sleep() потому что пауза селениума уходит в ошибку почему-то
    правильнее наверное все таки паузу селениума использовать'''

    #driver = uc.Chrome()  # инициализация драйвера

    with webdriver.Chrome() as driver:
        url = "https://ozon.ru"  # url озона

        driver.get(url)  # гет на юрл
        time.sleep(3)  # пауза после гета на юрл

        update_input = driver.find_element(By.ID, 'reload-button')  # определение кнопки "Обновить"
        update_input.send_keys(Keys.ENTER)  # нажатие энтер обновить
        time.sleep(2)  # пауза после обновления страницы
        
        find_input = driver.find_element(By.NAME, 'text')  # находит строку поиска
        find_input.clear()  # на всякий, очищает строку
        find_input.send_keys(item_name)  # вводит в строку поиска наш итем
        time.sleep(2)  # немного подождет после ввода в строку поиска наименования товара
        
        find_input.send_keys(Keys.ENTER)  # жмет энтер для поиска 
        time.sleep(2)  # ждет загрузки страницы с товарами

        # сортировка товаров на странице
        # к юрл добавляется &sorting=price, соответсвенно сортируется по цене
        current_url = driver.current_url + "&sorting=price" 
        driver.get(current_url)  # гет на юрл страницы отсортированных товаров
        time.sleep(2)  # ожидаение после сортировки товаров 

        #page_down(driver=driver)  # вызывает функцию скролинга страницы
        #time.sleep(5)  # ожидание после вызова функции скролинга


def test():
    with webdriver.Chrome(ChromeDriverManager().install()) as driver:
        driver.get("https://ya.ru")
        time.sleep(5)
        print("Ok")
      

def main() -> None:
    get_products_links()


if __name__ == '__main__':
    main() 


