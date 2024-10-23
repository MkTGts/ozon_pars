from typing import Generator


def page_down(driver):
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
    '''Функция заполняющая создает генератор ссылок на карточки товара
    функция избавляется от дублей ссылок и в тоже время сохраняет порядок.
    за счет того, что добавляет ссылки через одну '''
    num: int = 0  # счетчик

    # проходит циклом и добавляет ссылки через одну
    for link in find_links:
        if num % 2 == 0:
            yield link
        num += 1

            


