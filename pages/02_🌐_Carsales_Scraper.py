import datetime
import time
from pathlib import Path
from typing import Optional

import pandas as pd
import streamlit as st
from attrs import asdict
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from car import Car
import random


def do_search(
    min_year: Optional[int], max_year: Optional[int], make: str, model: str
) -> list[Car]:

    options = Options()
    options.headless = True
    driver = webdriver.Firefox(options=options)

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

    title = driver.find_elements(By.CLASS_NAME, 'title')

    if not title:

        if 'captcha' in driver.page_source:
            st.error('carsales thinks you are a robot, try a new ip address.')
        else:
            st.error('did not load, try again.')

        driver.save_screenshot('error.png')
        st.image('error.png')
        return []

    title = title[0]

    driver.save_screenshot('success.png')
    st.image('success.png')

    num_search_results = title.text.split(' ')[0]
    num_search_results = num_search_results.replace(',', '').strip()
    num_search_results = int(num_search_results)
    if num_search_results > 1000:
        st.error(
            f"Found {num_search_results} results, carsales doesn't like over 1000, try splitting the search."
        )
        return []

    if num_search_results == 0:
        st.error(f'found no results, try again.')
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
        new_list = [Car.from_card_webelement(card) for card in page_listings]
        car_list.extend(new_list)
        titles = [car.title for car in new_list]
        titles.reverse()
        with st.expander(f'Page {current_page+1}'):
            st.text('\n'.join(titles))

        progress_bar.progress(len(car_list) / num_search_results)
        sleep_time = random.randrange(3, 10)
        time.sleep(sleep_time)   # to avoid being blocked as a bot
        if len(car_list) < num_search_results:
            pagination_div = driver.find_elements(
                By.CSS_SELECTOR, 'ul.pagination'
            )
            if pagination_div:
                next_page_elem = pagination_div[0].find_elements(
                    By.PARTIAL_LINK_TEXT, 'Next'
                )
            else:
                st.warning('could not find next page, stopping.')
                driver.save_screenshot('error2.png')
                st.image('error2.png')
                break
            if next_page_elem:
                next_page_link = next_page_elem[0].get_attribute('href')
                driver.get(next_page_link)
            else:
                st.warning('could not find next page, stopping.')
                break
        else:
            break

        current_page += 1

    driver.close()
    dict_list = [asdict(car) for car in car_list]
    df = pd.DataFrame.from_records(dict_list)
    st.session_state['cars_df'] = df
    return car_list


def main():
    st.write('# Carsales Scraper')

    make = st.sidebar.text_input('Make')
    model = st.sidebar.text_input('Model')

    next_year = datetime.date.today().year + 1
    year_range = range(next_year, 1990, -1)
    min_year = st.sidebar.selectbox('Min Year', year_range, index=4)
    max_year = st.sidebar.selectbox('Max Year', year_range, index=0)

    if st.sidebar.button('Do Search'):
        do_search(min_year, max_year, make, model)

    if 'cars_df' in st.session_state:
        df = st.session_state['cars_df']
        st.dataframe(df)
        filename = '_'.join(
            [
                make.lower(),
                model.lower(),
                str(min_year),
                str(max_year),
            ]
        ).replace(' ', '_')
        path = Path.cwd().joinpath('data', filename).with_suffix('.csv')
        st.sidebar.markdown("""---""")
        st.sidebar.markdown('## Save File')
        if path.exists():
            st.sidebar.markdown(
                f'{filename} already exists. This will overwrite.'
            )
        if st.sidebar.button('Save to CSV'):
            if not path.parent.exists():
                path.parent.mkdir()
            df.to_csv(path)


if __name__ == '__main__':
    main()
