import json
import time
from datetime import datetime
from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from functions import page_down, links_generator


def get_products_links(item_name:str="наушники беспроводные"):
    '''Собирает ссылки на товару по запросу, переданному аргументом в функцию
    Для пауз используется стандартный time.sleep() потому что пауза селениума уходит в ошибку почему-то
    правильнее наверное все таки паузу селениума использовать
    Во внутрь карточек проваливаться придется, так-как информации на общей странице недостаточно.'''

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

        ### ###
        #page_down(driver=driver)  # вызывает функцию скролинга страницы
        #time.sleep(5)  # ожидание после вызова функции скролинга
        ### ###

        # поиск ссылок на страницы товаров
        try:
            find_links = driver.find_elements(By.CLASS_NAME, 'tile-hover-target') # поиск по тегу
            print(type(find_links))

            '''словарь пронумерованных ссылок. для того чтобы избавиться от дублей ссылок используется 
            фунция list_generator из functions.py которая просто берет ссылки через одну
            дубли ссылок появляются из-за ссылок на картинке и на наименовании товара'''
            result_urls = {
                j: k for j, k in enumerate(
                    (f'{link.get_attribute("href")}' for link in links_generator(find_links))
                )
            }
            
            # запись в файл json, название которого состоит из имени ресурса, даты и времени парсинга
            with open(
                f'{datetime.strftime(datetime.now(), "./ozon_links/ozon_links_d%d%m%y_t%H%M%S.json")}', 'w', encoding='utf-8'
                ) as file:
                json.dump(result_urls, file, indent=4, ensure_ascii=False)

            print("[+] Ссылки на товары добавлены")  # сообщение о удачном сборе ссылок карточек
        except:
            print("[!] По дороге что-то сломалось.")  # если что-то пошло не так      


def main() -> None:
    get_products_links()

if __name__ == '__main__':
    main() 


