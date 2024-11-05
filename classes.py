from typing import Generator
import json
import time
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup


# класс парсера озона
class Ozon():
    # словарь из возможных признаков сортировки
    sign_sorting: dict = {
            'price_l': '&sorting=price',  # по возрастанию цены
            'price_h': '&sorting=price_desc',  # по убыванию цены
            'new': '&sorting=new',  # по новизне
            'sale': '&sorting=discount',  # по распродажам
            'rating': '&sorting=rating'  # по рейтингу
        }

    
    def __init__(self, driver: webdriver, item_name: str, sign: str="price_l", 
                timing=2, count_cards=5) -> None:
        self.driver = driver  # вебдрайвер
        self.url = "https://ozon.ru"  # основной url озона
        self.item_name = item_name  # наименование товара который будет искать в поисковой строке озона
        self.sign = __class__.sign_sorting[sign]  # признак сортировки по которому будет сортировать полученый список товаров
        self.count_cards = count_cards  # количество проходимых карточек товаров
        self.timing = timing  # время ожиданий в общем случае


    def page_down(self) -> None:
        '''JS функция скроллинга страницы '''
        self.driver.execute_script('''
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
        

    def del_to_not_dig(self, s: str) -> None:
        # метод удаляет все символы, неявляющиеся цифрами. для удаления лишнего из цен
        for dig in s:  # проходит циклом по строке цены
            if not dig.isdigit():  # если не цифра
                s = s.replace(dig, '')  # заменяет символ 

        n = 1
        # добавление пробелов в тысячах
        for d in range(len(s))[::-1]:
            if n == 3:
                s = s[:d] + ' ' + s[d:]
                n = 0
            else:
                n += 1
                continue
       
        return s + ' ₽'


    def links_generator(self, find_links: list[str]) -> Generator:
        '''Метод создает генератор ссылок на карточки товара
        функция избавляется от дублей ссылок и в тоже время сохраняет порядок.
        за счет того, что добавляет ссылки через одну '''
        num: int = 0  # счетчик

        # проходит циклом и добавляет ссылки через одну
        for link in find_links:
            if num % 2 == 0:
                yield link
            num += 1


    def searcher_links(self) -> dict[int: str] | None:
        '''Метод поиска ссылок на страницы товаров. Находит ссылки и записывает в json файл. После возвращает словарь, для прохода по карточкам товара в main.py
        работает. Создает словарь, проходясь по генератору ссылок.'''
        try:
            find_links = self.driver.find_elements(By.CLASS_NAME, 'tile-hover-target') # поиск по тегу
            print(type(find_links))

            '''словарь пронумерованных ссылок. для того чтобы избавиться от дублей ссылок используется 
            фунция list_generator из functions.py которая просто берет ссылки через одну.
            вообще дубли ссылок появляются из-за того что ссылка есть на картинке и на наименовании товара'''
            result_links = {
                j: k for j, k in enumerate(
                    (f'{link.get_attribute("href")}' for link in self.links_generator(find_links))
                )
            }
            
            # запись в файл json, название которого состоит из имени ресурса, даты и времени парсинга
            with open(
                f'{datetime.strftime(datetime.now(), "./ozon_data/links/ozon_links_d%d%m%y_t%H%M%S.json")}', 'w', encoding='utf-8'
                ) as file:
                json.dump(result_links, file, indent=4, ensure_ascii=False)

            print("[+] Ссылки на товары добавлены")  # сообщение о удачном сборе ссылок карточек
            return result_links
        except:
            print("[!] По дороге что-то сломалось.")  # если что-то пошло не так   


    def product_data_pars(self, url: str) -> dict[str, str]:
        '''Метод открывает карточку товара в новой вкладке собирает информацию о товаре из карточкию.
        На вход принимает url карточки товара.'''
        self.driver.switch_to.new_window('tab')  # открывает новую вкладку 
        self.driver.get(url)  # гет на юрл карточки товара

        # находит артикул товара
        product_id = self.driver.find_element(
            By.XPATH, '//div[contains(text(),"Артикул:")]'
        ).text.lstrip("Артикул: ")

        page = str(self.driver.page_source)  # сохраняет страницу
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
            #'product_stat': product_stat, 
            'product_stars': product_stars,
            'product_reviews': product_reviews, 
            'product_card_price': self.del_to_not_dig(product_card_price),  # добалено удаление лишних символов из цены
            'product_discount_price': self.del_to_not_dig(product_discount_price), 
            'product_full_price': self.del_to_not_dig(product_full_price)
        }

        self.driver.close()  # закрывает окно карточки товара    
        self.driver.switch_to.window(self.driver.window_handles[0])  # переходит на дефолтную страницу

        return product_data
    

    def go_get(self) -> None:
        '''Первый гет на осной юрл озона'''
        self.driver.get(self.url)  # отправет гет запрос
        time.sleep(self.timing)  # ждет 2 сек


    def go_bypassing(self) -> None:
        '''При первом гет запросе включается защита от бота.
        Этот метод нажимает на вылезающую кнопку обновить и открывается главную страницу озон'''
        try:
            self.driver.find_element(By.ID, 'reload-button').click()  # определение кнопки "Обновить" и клик на нее
            time.sleep(self.timing)  # пауза после обновления страницы
        except:
            time.sleep(self.timing)
            self.go_bypassing()


    def go_select_locatiion(self) -> dict:
        '''Озон авто определяет местопложение и этот метод клик по кнопке подвердить в сплывающем окне определнному местополжению
        спорная на самом деле реализация, но вроде работает пока, за счет ожидания в если не появилась кнопка'''
        try:
            # находим кнопку
            self.driver.find_element(By.CSS_SELECTOR, 'div.vue-portal-target  button').click()  # кликаем
            time.sleep(self.timing)
            return None
        except:
            # если кнопки еще нет, вернулась ошибка. ждет 2 сек и опять пробует
            time.sleep(self.timing)
            self.go_select_locatiion(self.driver)


    def go_search(self) -> None:
        '''Метод вводит в поисковую строку озона нужное наименование и начнает поиск.'''
        find_input = self.driver.find_element(By.NAME, 'text')  # находит строку поиска
        find_input.clear()  # на всякий, очищает строку
        find_input.send_keys(self.item_name)  # вводит в строку поиска наш итем
        time.sleep(0.5)  # немного подождет после ввода в строку поиска наименования товара
        
        find_input.send_keys(Keys.ENTER)  # жмет энтер для поиска 
        time.sleep(self.timing)  # ждет загрузки страницы с товарами

    
    def go_sorting(self) -> None:
        '''Cортировка товаров на странице. Стандартная сортировка по возрастанию цен.
        K юрл добавляется сортировка'''
        current_url = f'{self.driver.current_url}{self.sign}'
        self.driver.get(current_url)  # гет на юрл страницы отсортированных товаров
        time.sleep(self.timing)  # ожидаение после сортировки товаров 

    
    def _go_scroll(self) -> None:
        '''Скролинг страницы. Пока не используется.'''
        self.page_down(self.driver)  # вызывает функцию скролинга страницы
        time.sleep(self.timing)  # ожидание после вызова функции скролинга


    def go_product_datas(self) -> None:
        # записывает данные собранные со всех карточек товаров
        products_data: list = []

        # проходит циклом по словарю ссылок
        for n, url in self.searcher_links().items():
            try:  # если ошибок нет
                data: dict = self.product_data_pars(url=url)  # собирает данные с карточки товара в словарь
                print(f"[+] С ссылки №{n} данные успешно собраны.")  # принутет что все норм
                products_data.append(data)  # и запись в общую коллекцию
            except Exception as err:  # если что-то пошло не так, сообщает об этом
                print(f'[-] При работе с ссылкой №{n} возникла ошибка {err}.')
            if n == self.count_cards:  # для теста ограничение на проход только по 3-м ссылкам
                break

                # записывает полученные данные в результурющий json
        with open(
            datetime.strftime(datetime.now(), "./ozon_data/cards_data/OZON_PRODUCT_DATA_d%d%m%y--t%H-%M-%S.json"), 'w', encoding="utf-8"
            ) as file:
            json.dump(products_data, file, indent=4, ensure_ascii=False)


# класс парсера wb
class Wildberries():
    # словарь ключей для сортировки товаров по признаку
    sign_sorting: dict = {
            'pl': '&sort=priceup',  # по возрастанию цены
            'ph': '&sort=pricedown',  # по убыванию цены
            'new': '&sort=newly',  # по новизне
            'sale': '&sort=benefit',  # по распродажам
            'rate': '&sort=rate'  # по рейтингу
        }


    def __init__(self, driver: webdriver, item_name: str, sign: str="rate", count_cards=3, timing=2) -> None:
        self.url = "https://www.wildberries.ru/"  # url wildberries
        self.driver = driver  # объект дравйвера
        self.timing = timing  # время ожидания в общем случае
        self.item_name = item_name  # наименование товара для поискового запроса
        self.sign = __class__.sign_sorting[sign]  # признак сортировки по которому будет сортировать полученый список товаров
        self.count_cards = count_cards  # количество проходимых карточек товаров


    def _get_to_main_page(self) -> None:
        '''Функция гет запрос на страницу, с внесенесенными данными по поиску и сортировке товаро на страницы, в саму ссылку.
        Пока это работает и естественно намного быстрее ручного ввода в строку поиск.'''
        self.url = f"https://www.wildberries.ru/catalog/0/search.aspx?{self.sign.lstrip('&')}&search={self.item_name}"  # измененый юрл WB
        self.driver.get(self.url)  # гет на этот юрл
        time.sleep(self.timing)  # ожидание 


    def page_down(self) -> None:
        '''JS функция скроллинга страницы '''
        self.driver.execute_script('''
                                const scrollStep = 20; // Размер шага прокрутки (в пикселях)
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


    def go_get(self) -> None:
        '''Метод гет запроса на главную страницу ВБ'''
        self.driver.get(self.url)  # гет запрос 
        time.sleep(self.timing)  # ожидание


    def go_search(self) -> None:
        '''Метод вводит в поисковую строку ВБ нужное наименование товара и начинает поиск.'''
        find_input = self.driver.find_element(By.ID, 'searchInput')  # находит строку поиска
       # find_input.clear()  # на всякий случай строка для поиска очищается
        # time.sleep(0.5)
        find_input.send_keys(self.item_name)  # вводит в строку поиска наш запрос
        time.sleep(self.timing)  # небольшое ожидание после ввода

        find_input.send_keys(Keys.ENTER)  # жмет энтер
        time.sleep(self.timing)  # ожидание после начала поиска


    def go_sorting(self) -> None:
        '''Cортировка товаров на странице. Стандартная сортировка по рейтингу.
        K юрл добавляется запрос сортировка'''
        current_url = f'{self.driver.current_url}{self.sign}'
        self.driver.get(current_url)  # гет на юрл страницы отсортированных товаров
        time.sleep(self.timing)  # ожидаение после сортировки товаров 


    def _go_scroll(self) -> None:
        '''Скролинг страницы. Используется для открытия полного кода страницы.'''
        self.page_down()  # вызывает функцию скролинга страницы
        time.sleep(self.timing)  # ожидание после вызова функции скролинга


    def searcher_links(self) -> dict[int: str] | None:
        '''Метод поиска ссылок на страницы товаров. Находит ссылки и записывает в json файл. После возвращает словарь, для прохода по карточкам товара'''
        
        try:
            self._go_scroll()  # немного скрол виниз, для открытия страницы
            time.sleep(self.timing)  # ожидание после прокрутки

            soup = BeautifulSoup(self.driver.page_source, 'lxml')  # создание супа страницы с товарами

            links_dict: dict[int: str] = {} # словарь под ссылки на товары

            # проходится циклам по всем совпадениям с нумерацией
            for n, tag in enumerate(soup.find_all('a', class_='product-card__link j-card-link j-open-full-product-card')):
                links_dict[n] = tag.get('href')  # записывает в словарь по ключу - номер ссылки

            # открывает json файл для записи    
            with open(f'{datetime.strftime(datetime.now(), "./wb_data/links/wb_links_d%d%m%y_t%H%M%S.json")}',
                    'w', encoding='utf-8') as file:
                json.dump(links_dict, file, indent=4, ensure_ascii=False)

            print(f'[INFO] Добавлено {n + 1} ссылок.')
            return links_dict  # возваращает словарь со ссылками на карточки товаров
        except Exception as err:
            print(f'[ERROR] Возникла ошибка {err}')

    
    def del_to_not_dig(self, s: str) -> None:
        # метод удаляет все символы, неявляющиеся цифрами. для удаления лишнего из цен
        for dig in s:  # проходит циклом по строке цены
            if not dig.isdigit():  # если не цифра
                s = s.replace(dig, '')  # заменяет символ 

        n = 1
        # добавление пробелов в тысячах
        for d in range(len(s))[::-1]:
            if n == 3:
                s = s[:d] + ' ' + s[d:]
                n = 0
            else:
                n += 1
                continue
       
        return s + ' ₽'


    def product_data_pars(self, url: str) -> dict[str, str]:
        '''Метод открывает карточку товара в новой вкладке собирает информацию о товаре из карточкию.
        На вход принимает url карточки товара.'''
        self.driver.switch_to.new_window('tab')  # открывает новую вкладку 
        self.driver.get(url)  # гет на юрл карточки товара
        self._go_scroll()  # скролинг для открытия html кода
        time.sleep(self.timing)  # немного подождать

        page = str(self.driver.page_source)  # сохраняет страницу
        soup = BeautifulSoup(page, 'lxml')  # создает суп

        # цикл ожидания пока не появятся все нужные теги
        while not soup.find(
                'span', class_='price-block__price'
            ):
            time.sleep(0.5)
            page = str(self.driver.page_source)  # сохраняет страницу
            soup = BeautifulSoup(page, 'lxml')  # создает суп

        product_id = soup.find('span', id='productNmId').text.strip()  # находит артикул товара

        product_name = soup.find('h1', class_='product-page__title').text.strip()  # находит наименование товара

        try:
            # находит количество звезд у товара
            product_stars = soup.find('p', class_='product-page__reviews-icon address-rate-mini address-rate-mini--sm').text.strip()
            product_reviews = soup.find('p', class_='product-page__reviews-text').text.strip()  # находит количество оценок у товара
        except:  # если ошибка то Ноны
            product_stars = None
            product_reviews = None

        # находит цену по карте wb и со скидкой без карты, в одну строку
        try:
            # находит часть когда в котором цены и забирает от туда текс, в котором одновременно обе цены и создает список разделителем ₽
            prices = soup.find(
                'span', class_='price-block__price'
            ).text.strip().split('₽')

            # первая цена это цена по карте
            product_discount_price = self.del_to_not_dig(prices[0].strip())

            if prices[1]:  # если есть вторая цена, тогда присваивает ее переменной цены со скидкой
                product_card_price = self.del_to_not_dig(prices[0].strip())
                product_discount_price = self.del_to_not_dig(prices[1].strip())
            else:  # если второй нет, то цена скидкой нан
                product_discount_price = None
        except Exception as err:
            # если исключение врзникает, значит такой тег не найден, и значит цен со скидками нет None
            product_card_price = None
            product_discount_price = None
            print(f'[ERROR] Похоже что цена только без скидки...{err}')

        # находит полную цену без скидки
        product_full_price = self.del_to_not_dig(soup.find('del', class_='price-block__old-price').text.strip())

        # словарь со всеми собранными данными
        product_data = {
            'product_id': product_id,
            'product_name': product_name,
            'product_stars': product_stars,
            'product_reviews': product_reviews, 
            'product_card_price': product_card_price,
            'product_discount_price': product_discount_price, 
            'product_full_price': product_full_price
        }

        self.driver.close()  # закрывает окно карточки товара    
        self.driver.switch_to.window(self.driver.window_handles[0])  # переходит на дефолтную страницу

        print(product_data)

        return product_data


    def go_product_datas(self) -> None:
        # записывает данные собранные со всех карточек товаров
        products_data: list = []  # список под словари с данными с карточек товаров

        # проходит циклом по словарю ссылок
        for n, url in self.searcher_links().items():
            try:  # если ошибок нет
                data: dict = self.product_data_pars(url=url)  # собирает данные с карточки товара в словарь
                print(f"[INFO] С ссылки №{n} данные успешно собраны.")  # принутет что все норм
                products_data.append(data)  # и запись в общую коллекцию
            except Exception as err:  # если что-то пошло не так, сообщает об этом
                print(f'[ERROR] При работе с ссылкой №{n} возникла ошибка {err}.')
            if n == self.count_cards:  # для теста ограничение на проход только по 3-м ссылкам
                break

                # записывает полученные данные в результурющий json
        with open(
            datetime.strftime(datetime.now(), "./wb_data/cards_data/WB_PRODUCT_DATA_d%d%m%y--t%H-%M-%S.json"), 'w', encoding="utf-8"
            ) as file:
            json.dump(products_data, file, indent=4, ensure_ascii=False)



