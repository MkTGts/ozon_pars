from selenium import webdriver
from classes import Ozon, Wildberries
import requests
import time
from bs4 import BeautifulSoup
import lxml
import re


def go_to_ozon():
    '''Парсер озона'''
    with webdriver.Chrome() as driver:
        ozon_object = Ozon(driver=driver, item_name='наушники беспроводный', count_cards=3, timing=1)  # создается объект класса Ozon
        ozon_object.go_get()  # гет на главную страницу озона
        ozon_object.go_bypassing()  # обход защиты от бота
        #ozon_object.go_select_locatiion()  # выбор предлагаемого местоположения
        ozon_object.go_search()  # ввод наименования в поисковую строку и поиск
        ozon_object.go_sorting()  # сортировка по признаку
        ozon_object.go_product_datas()  # сбор данных с карточек товаров и запись в json файл


def go_to_wb():
    '''Парсер WildBerries'''
    with webdriver.Chrome() as driver:
        wb_object = Wildberries(driver, item_name="монитор")  # созадн объект класса Wildberries
        wb_object.go_get()  # отправляется гет запрос на главную страницу ВБ
        wb_object.go_search()  # вводится запрос в поисковую строку и начинается поиск
        wb_object.go_sorting()  # сортиорвка товаров по признаку
        wb_object.go_product_datas()  # сбор данных с карточек товаров и запись в json файл


def _go_to_wb():
    '''Парсер WildBerries по изменяемой ссылке'''
    with webdriver.Chrome() as driver:
        wb_object = Wildberries(driver, item_name="монитор")  # созадн объект класса Wildberries
        wb_object._get_to_main_page()  # 
        wb_object.go_product_datas()  # сбор данных с карточек товаров и запись в json файл

        

if __name__ == "__main__":
    #_go_to_wb()   
    go_to_ozon()
