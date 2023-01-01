import re
from typing import Optional, Self

from attrs import frozen
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement


@frozen
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
