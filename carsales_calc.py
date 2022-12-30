import configparser
import datetime
import os.path
import re
from typing import Optional, Self

import matplotlib.pyplot as plt
import numpy
from attrs import define, asdict
from selenium import webdriver

from selenium.webdriver.common.by import By

# from selenium.webdriver.firefox.options import Options
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
import undetected_chromedriver as uc

import time
import streamlit as st
import pandas as pd
from pathlib import Path


@define
class Car:
    link: str
    title: str
    year: int
    marketing_year: str
    drive_away_price: Optional[int]
    ex_gov_price: Optional[int]
    price_text: str
    price_info: str
    kms: int
    id: str
    category: str
    make: str
    model: str
    badge: str
    state: str
    body_style: str
    transmission: str
    engine: str
    seller_type: Optional[str]
    build_date: Optional[str] = None
    odometer: Optional[int] = None

    @classmethod
    def from_card_webelement(cls, card: WebElement) -> Self:
        link = card.find_element(By.TAG_NAME, 'a').get_attribute('href')
        title = card.find_element(By.TAG_NAME, 'h3').text

        print('Adding', title)
        year = int(title.split(' ')[0])

        # TODO: split into drive away and ex gov charges
        price_text = card.find_element(By.CSS_SELECTOR, 'div.price').text
        price_info = card.find_element(By.CLASS_NAME, 'price-info').text
        price_match = re.match(r'\$([\d,]+)', price_text)
        if price_match is not None:
            price = price_match.groups()[0].replace(',', '')
            price = int(price)
        else:
            price = None

        price_info_match = re.match(r'\$([\d,]+)', price_info)
        if price_info_match is not None:
            price_info_price = price_info_match.groups()[0].replace(',', '')
            price_info_price = int(price_info_price)
        else:
            price_info_price = None

        drive_away_price = (
            price
            if any('Drive Away' in text for text in [price_text, price_info])
            else None
        )

        ex_gov_price = (
            price
            if all(
                'Drive Away' not in text for text in [price_text, price_info]
            )
            else price_info_price
        )

        details_list = card.find_element(By.CLASS_NAME, 'key-details')
        details_items = details_list.find_elements(By.TAG_NAME, 'li')
        details = {}
        details = {
            item.get_attribute('data-type')
            .lower()
            .replace(' ', '_'): item.text
            for item in details_items
        }
        details['id'] = card.get_attribute('id')
        details['category'] = card.get_attribute('data-webm-vehcategory')
        details['make'] = card.get_attribute('data-webm-make')
        details['model'] = card.get_attribute('data-webm-model')
        details['state'] = card.get_attribute('data-webm-state')

        class_ = card.get_attribute('class').strip()
        if 'cs-select' in class_:
            seller_type_elem = card.find_element(By.CLASS_NAME, 'ad-type')
        else:
            seller_type_elem = card.find_element(By.CLASS_NAME, 'seller-type')

        seller_type = re.sub(r'[\d\.]+', '', seller_type_elem.text).strip()

        if 'odometer' in details:
            kms_match = re.match(r'([\d,]+).*km', details['odometer'])
            kms = 0
            if kms_match is not None:
                kms = int(kms_match.groups()[0].replace(',', ''))
        else:
            kms = 0

        to_remove = [
            str(year),
            details['make'],
            details['model'],
            r'MY[\.\d]+',
            'Auto',
        ]
        badge = title
        for sub in to_remove:
            badge = re.sub(sub, '', badge)

        details['badge'] = badge.strip()
        marketing_year = re.search(r'(MY[\.\d]+)', title)
        if marketing_year is not None:
            marketing_year = marketing_year.groups()[0]
        else:
            marketing_year = ''

        car = cls(
            link,
            title,
            year,
            marketing_year,
            drive_away_price,
            ex_gov_price,
            price_text,
            price_info,
            kms,
            seller_type=seller_type,
            **details,
        )

        return car


def get_average(list):
    price_list = []
    for item in list:
        price = item[4]
        price_list.append(price)
    return numpy.average(price_list)


def do_search(
    min_year: Optional[int], max_year: Optional[int], make: str, model: str
) -> list[Car]:

    options = Options()
    # options.headless = True
    driver = driver = uc.Chrome(options=options)

    print('Searching Carsales')
    driver.get(
        'https://www.carsales.com.au/cars/?q=(And.(C.Make.'
        + make
        + '._.Model.'
        + model
        + '.)_.Year.range('
        + str(min_year)
        + '..'
        + str(max_year)
        + ')._.Condition.Used.)&sort=~Price'
    )

    title = WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CLASS_NAME, 'title'))
    )

    num_search_results = title.text.split(' ')[0]
    num_search_results = num_search_results.replace(',', '').strip()
    num_search_results = int(num_search_results)
    if num_search_results > 1000:
        st.error(
            f"Found {num_search_results} results, carsales doesn't like over 1000, try splitting the search."
        )
        return []

    st.info(f'Found {num_search_results} results, scraping details...')

    current_page = 0
    car_list = []

    progress_bar = st.progress(0)
    while True:
        print('Loading page', str(current_page))
        page_listings = driver.find_elements(
            By.CSS_SELECTOR, 'div.listing-item'
        )
        car_list.extend(
            [Car.from_card_webelement(card) for card in page_listings]
        )
        progress_bar.progress(len(car_list) / num_search_results)
        time.sleep(3.0)   # to avoid being blocked as a bot
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

    driver.close()
    dict_list = [asdict(car) for car in car_list]
    df = pd.DataFrame.from_records(dict_list)
    st.session_state['cars_df'] = df
    return car_list


def main():

    make = st.sidebar.text_input('Make')
    model = st.sidebar.text_input('Model')

    next_year = datetime.date.today().year + 1
    year_range = range(next_year, 1990, -1)
    min_year = st.sidebar.selectbox('Min Year', year_range, index=4)
    max_year = st.sidebar.selectbox('Max Year', year_range, index=0)

    st.sidebar.button(
        'Do Search', on_click=do_search, args=(min_year, max_year, make, model)
    )

    if 'cars_df' in st.session_state:
        df = st.session_state['cars_df']
        st.dataframe(df)
        filename = f'{make.lower()}_{model.lower()}_{min_year}_{max_year}.csv'
        path = Path.cwd().joinpath('data', filename)
        st.markdown('## Save File')
        if path.exists():
            st.markdown(f'{filename} already exists. This will overwrite.')
        if st.button('Save to CSV'):
            if not path.parent.exists():
                path.parent.mkdir()
            df.to_csv(path)

    # x = [x.year for x in car_list]
    # y = [x.price for x in car_list]
    # plt.scatter(x, y)
    # z = numpy.polyfit(x, y, 1)
    # p = numpy.poly1d(z)

    # plt.plot(x, p(x), 'r--')

    # plt.show()


if __name__ == '__main__':
    main()
