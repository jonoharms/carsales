import configparser
import datetime
import os.path
import re
from typing import Optional, Self

import matplotlib.pyplot as plt
import numpy
from attrs import define
from selenium import webdriver

from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.remote.webelement import WebElement


@define
class Car:
    link: str
    title: str
    year: int
    details: dict
    price: Optional[int]
    price_text: str

    @classmethod
    def from_card_webelement(cls, card: WebElement) -> Self:
        link = card.find_element(By.TAG_NAME, 'a').get_attribute('href')
        title = card.find_element(By.TAG_NAME, 'h3').text

        print('Adding', title)
        year = int(title.split(' ')[0])
        price_text = card.find_element(By.CSS_SELECTOR, 'div.price').text
        price_match = re.match(r'\$(\d+,\d+)', price_text)
        if price_match is not None:
            price = price_match.groups()[0].replace(',', '')
            price = int(price)
        else:
            price = None

        details_list = card.find_element(By.CLASS_NAME, 'key-details')
        details_items = details_list.find_elements(By.TAG_NAME, 'li')
        details = {}
        details = {
            item.get_attribute('data-type'): item.text
            for item in details_items
        }

        car = cls(
            link,
            title,
            year,
            details,
            price,
            price_text,
        )

        return car


def get_average(list):
    price_list = []
    for item in list:
        price = item[4]
        price_list.append(price)
    return numpy.average(price_list)


def main():
    options = Options()
    driver = webdriver.Firefox(options=options)

    user_make, user_model = ('Skoda', 'Superb')

    print('Searching Carsales')
    driver.get(
        'https://www.carsales.com.au/cars/?q=(And.(C.Make.'
        + user_make
        + '._.Model.'
        + user_model
        + '.)_.Year.range(2007..).)'
    )

    num_search_results = int(
        driver.find_element(By.CLASS_NAME, 'title').text.split(' ')[0]
    )

    current_page = 0
    car_list = []

    while True:
        print('Loading page', str(current_page))
        page_listings = driver.find_elements(
            By.CSS_SELECTOR, 'div.listing-item'
        )
        car_list.extend(
            [Car.from_card_webelement(card) for card in page_listings]
        )

        if len(car_list) < num_search_results:
            pagination_div = driver.find_element(
                By.CSS_SELECTOR, 'ul.pagination'
            )
            next_page_link = pagination_div.find_element(
                By.PARTIAL_LINK_TEXT, 'Next'
            ).get_attribute('href')
            driver.get(next_page_link)
        else:
            break

        current_page += 1

    x = [x.year for x in car_list]
    y = [x.price for x in car_list]
    plt.scatter(x, y)
    z = numpy.polyfit(x, y, 1)
    p = numpy.poly1d(z)

    plt.plot(x, p(x), 'r--')

    plt.show()


if __name__ == '__main__':
    main()
