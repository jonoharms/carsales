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
        car_link = card.find_element(By.TAG_NAME, 'a').get_attribute('href')
        car_title = card.find_element(By.TAG_NAME, 'h3').text

        print('Adding', car_title)
        car_year = int(car_title.split(' ')[0])
        car_price_text = card.find_element(By.CSS_SELECTOR, 'div.price').text
        car_price_match = re.match(r'\$(\d+,\d+)', car_price_text)
        if car_price_match is not None:
            price = car_price_match.groups()[0].replace(',', '')
            car_price = int(price)
        else:
            car_price = None

        details_list = card.find_element(By.CLASS_NAME, 'key-details')
        details_items = details_list.find_elements(By.TAG_NAME, 'li')
        car_details = {}
        for item in details_items:
            car_details[item.get_attribute('data-type')] = item.text

        car = cls(
            car_link,
            car_title,
            car_year,
            car_details,
            car_price,
            car_price_text,
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

    # setup config file. if it exists, load it
    config = configparser.ConfigParser()
    if os.path.isfile('carsales_calc.ini'):
        config.read('carsales_calc.ini')
        user_settings = config['user']
        user_state = user_settings['State']
        if 'Transmission' in user_settings:
            user_transmission = user_settings['Transmission']
        else:
            transmission_switch = False
        if 'Min price' in user_settings:
            price_min, price_max = (
                user_settings['Min price'],
                user_settings['Max price'],
            )
        else:
            price_switch = False
        kms_min, kms_max = user_settings['Min kms'], user_settings['Max kms']
    else:
        config.add_section('user')
        user_settings = config['user']
        print('Enter your State')
        user_state = input('> ')
        user_settings['State'] = user_state
        print('Enter your Transmission')
        user_transmission = input('> ')
        if user_transmission == '':
            transmission_switch = False
        else:
            user_settings['Transmission'] = user_transmission
        print('Enter your price range separated by commas')
        user_price_range = input('> ')
        if user_price_range == '':
            price_switch = False
        else:
            price_min, price_max = user_price_range.replace(' ', '').split(',')
            user_settings['Min price'] = price_min
            user_settings['Max price'] = price_max
        print('Enter your KM range separated by commas')
        user_kms_range = input('> ')
        kms_min, kms_max = user_kms_range.replace(' ', '').split(',')
        user_settings['Min kms'] = kms_min
        user_settings['Max kms'] = kms_max
        print('Saving config file.')
        with open('carsales_calc.ini', 'w') as configfile:
            config.write(configfile)

    print('Enter car make and model')
    # car_choice = input('> ')

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
