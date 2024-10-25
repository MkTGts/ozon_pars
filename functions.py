from typing import Generator
import json
import time
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.common.keys import Keys


def page_down(driver: webdriver) -> None:
    '''JS функция скроллинга страницы '''
    driver.execute_script('''
                            const scrollStep = 200; // Размер шага прокрутки (в пикселях)
                            const scrollInterval = 100; // Интервал между шагами (в миллисекундах)

                            const scrollHeight = document.documentElement.scrollHeight;
                            let currentPosition = 0;
                            const interval = setInterval(() => {
                                window.scrollBy(0, scrollStep);
                                currentPosition += scrollStep;

                                if (currentPosition >= scrollHeight) {
                                    clearInterval(interval);
                                }
                            }, scrollInterval);
                        ''')
    

def links_generator(find_links: list[str]) -> Generator:
    '''Функция создает генератор ссылок на карточки товара
    функция избавляется от дублей ссылок и в тоже время сохраняет порядок.
    за счет того, что добавляет ссылки через одну '''
    num: int = 0  # счетчик

    # проходит циклом и добавляет ссылки через одну
    for link in find_links:
        if num % 2 == 0:
            yield link
        num += 1


def searcher_links(driver: webdriver) -> None:
    '''Функция поиска ссылок на страницы товаров. Находит ссылки и записывает в json файл.
    работает. Создает словарь, проходясь по генератору ссылок.'''
    try:
        find_links = driver.find_elements(By.CLASS_NAME, 'tile-hover-target') # поиск по тегу
        print(type(find_links))

        '''словарь пронумерованных ссылок. для того чтобы избавиться от дублей ссылок используется 
        фунция list_generator из functions.py которая просто берет ссылки через одну.
        вообще дубли ссылок появляются из-за того что ссылка есть на картинке и на наименовании товара'''
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


def select_locatiion(driver: webdriver) -> None:
    '''Озон авто определяет местопложение и эта функция клик по кнопке подвердить в сплывающем окне определнному местополжению
    спорная на самом деле реализация, но вроде работает пока, за счет ожидания в если не появилась кнопка'''
    try:
        # находим кнопку
        driver.find_element(By.CSS_SELECTOR, 'div.vue-portal-target  button').click()  # кликаем
        time.sleep(2)
        return None
    except:
        # если кнопки еще нет, вернулась ошибка. ждет 2 сек и опять пробует
        time.sleep(2)
        searcher_links(driver)


def collect_product_info(driver: webdriver, url: str):
    '''Функция собирает информацию о товаре из карточки'''
    driver.switch_to.new_window('tab')  # открывает новую вкладку
    time.sleep(2)  # ждет 2 сек
    driver.get(url)  # гет на юрл карточки товара
    time.sleep(2)  # снова ждет

    # находит артикул товара
    product_id = driver.find_element(
        By.XPATH, '//div[contains(text(),"Артикул:")]'
    ).rstrip("Артикул: ")

    print(product_id)  # принтуем артикулы для теста (потом удалить)

            


            


