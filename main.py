from selenium import webdriver
from classes import Ozon


if __name__ == "__main__":
    with webdriver.Chrome() as driver:
        ozon_object = Ozon(driver=driver, item_name='наушники беспроводный', count_cards=3, timing=1)  # создается объект класса Ozon
        ozon_object.go_get()  # гет на главную страницу озона
        ozon_object.go_bypassing()  # обход защиты от бота
        ozon_object.go_select_locatiion()  # выбор предлагаемого местоположения
        ozon_object.go_search()  # ввод наименования в поисковую строку и поиск
        ozon_object.go_sorting()  # сортировка по признаку
        ozon_object.go_product_datas()  # сбор данных с карточек товаров и запись в json файл

