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
    st.write('# Carsales Scraper')

    make = st.sidebar.text_input('Make')
    model = st.sidebar.text_input('Model')

    next_year = datetime.date.today().year + 1
    year_range = range(next_year, 1990, -1)
    min_year = st.sidebar.selectbox('Min Year', year_range, index=4)
    max_year = st.sidebar.selectbox('Max Year', year_range, index=0)

    st.sidebar.button(
        'Do Search',
        on_click=do_search,  # type: ignore
        args=(min_year, max_year, make, model),
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


if __name__ == '__main__':
    main()
