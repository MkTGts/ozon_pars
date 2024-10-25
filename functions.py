from typing import Generator
import json
import time
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup


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


def product_data_pars(driver: webdriver, url: str):
    '''Функция открывает карточку товара в новой вкладке собирает информацию о товаре из карточкию.'''
    driver.switch_to.new_window('tab')  # открывает новую вкладку
    time.sleep(2)  # ждет 2 сек
    driver.get(url)  # гет на юрл карточки товара
    ###
    time.sleep(2)
    time.sleep(2)  # пауза после обновления страницы
    ###
    time.sleep(2)  # снова ждет

    # находит артикул товара
    product_id = driver.find_element(
        By.XPATH, '//div[contains(text(),"Артикул:")]'
    ).text.lstrip("Артикул: ")

    page = str(driver.page_source)  # сохраняет страницу
    soup = BeautifulSoup(page, 'lxml')  # создает суп

    # находит имя товара
    product_name = soup.find('div', attrs={'data-widget': 'webProductHeading'}).find(
        'h1').text.strip().replace('\t', '').replace('\n', ' ')
    
    # находит рейтинг статистику (рейтинг оценка и кол-во отзывов)
    product_stat = soup.find('div', attrs={"data-widget": 'webSingleProductScore'}).find("div").text.split(' • ')
    if len(product_stat) > 1:  # если строка разделилась символом • значит есть отзывы
        product_stars =  product_stat[0]  # рейтинг оценка
        product_reviews = product_stat[1].rstrip(' отзывов')  # количество отзывов
    else:  # если нет то ноны
        product_stars = None
        product_reviews = None

    # находит цену по озон карте
    try:
        product_card_price = soup.find('div', attrs={
            'data-widget': 'webSale'}).find('span').find('span').text
    except:
        product_card_price = None

    # дисконтная цена
    try:
        # находит общий тег цен без карты
        list_tag_prices = soup.find('span', string='без Ozon Карты').parent.parent.find('div').find_all('span')
        # цена со скидкой
        product_discount_price = list_tag_prices[0].text
        # если для списка больше 1 значит есть вторая цена, это полная цена 
        if len(list_tag_prices) > 1:
            product_full_price = list_tag_prices[1].text
    except:
        # в случае ошибки ноны
        product_discount_price = None
        product_full_price = None

    # словарь со всеми собранными данными
    product_data = {
        'product_id': product_id,
        'product_name': product_name,
        'product_stat': product_stat,
        'product_stars': product_stars,
        'product_reviews': product_reviews, 
        'product_card_price': product_card_price,
        'product_discount_price': product_discount_price, 
        'product_full_price': product_full_price
    }

    return product_data



with webdriver.Chrome() as driver:

    print(test1(driver=driver, url="https://www.ozon.ru/product/bane-adapter-cable-1-pcs-white-1015905521/?advert=ANwAvZANSMIoerm-5fLBNLmHATZrXrLVHRRPMe0SIDjdNA0h-1RFMu2r3lFLfnGfkyDMLcpp82TTMfikFuaV7mAm0vHmUoR530sLNE4dyWBAf77SyjOYisXeObnEd9DsAKQII10RyngiVrHFzHLWbF-1rLiXwQVNu__9HwvxDeqJrfvhA9VsIwPvYb18Bnd9hAOxkyCG4Ub49Q_kRuye4tmLuEkg47Fneiapa8JPPjFcy-EgqotDXJrxi7WBONWfn0J7ZNu613kgfB7ULH7WhkebH-klaKaKBZ5IC2vP_KJUf1BaehaFxtaGr9Y1AKFjjp09LRUWJAvH8j450lVk1WRxIrPPCWnWPONCC6p6mTQYNdSKqJSmwr0oI4QAvEsJ9gpJgw&avtc=1&avte=2&avts=1729873895&keywords=%D0%BF%D0%B5%D1%80%D0%B5%D1%85%D0%BE%D0%B4%D0%BD%D0%B8%D0%BA+iphone+aux", ))
            


