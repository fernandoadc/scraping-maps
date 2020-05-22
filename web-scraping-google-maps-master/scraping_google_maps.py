from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from bs4 import BeautifulSoup
import time
from datetime import datetime, timedelta
import argparse
import csv


driver = webdriver.Chrome(r'C:\chromedriver.exe')
url = 'https://www.google.com/maps/place/Pizza+na+M%C3%A3o/@-2.4261208,-54.7242552,17z/data=!3m1!4b1!4m7!3m6!1s0x9288f91d1bcf46a5:0xb07c15983543a9c6!8m2!3d-2.4261262!4d-54.7220665!9m1!1b1'
driver.get(url)
time.sleep(15)


def scroll():
    scrollable_div = driver.find_element_by_css_selector('div.section-layout.section-scrollbox.scrollable-y.scrollable-show')
    driver.execute_script('arguments[0].scrollTop = arguments[0].scrollHeight', scrollable_div)


def get_reviews(offset):

    # scroll to load reviews
    scroll()

    # wait for other reviews to load (ajax)
    time.sleep(10)

    # parse reviews
    response = BeautifulSoup(driver.page_source, 'html.parser')
    rblock = response.find_all('div', class_='section-review-content')
    parsed_reviews = []
    for index, review in enumerate(rblock):
        if index >= offset:
            parsed_reviews.append(parse(review))

    return parsed_reviews


def parse(review):

    item = {}

    id_review = review.find('button', class_='section-review-action-menu')['data-review-id']
    username = review.find('div', class_='section-review-title').find('span').text

    try:
        review_text = filter_string(review.find('span', class_='section-review-text').text)
    except Exception as e:
        review_text = None

    rating = float(review.find('span', class_='section-review-stars')['aria-label'].split(' ')[1])
    relative_date = review.find('span', class_='section-review-publish-date').text

    try:
        n_reviews_photos = review.find('div', class_='section-review-subtitle').find_all('span')[1].text
        metadata = n_reviews_photos.split('\xe3\x83\xbb')
        if len(metadata) == 3:
            n_photos = int(metadata[2].split(' ')[0].replace('.', ''))
        else:
            n_photos = 0

        idx = len(metadata)
        n_reviews = int(metadata[idx - 1].split(' ')[0].replace('.', ''))

    except Exception as e:
        n_reviews = 0
        n_photos = 0

    user_url = review.find('a')['href']

    item['id_review'] = id_review
    item['caption'] = review_text

    # depends on language, which depends on geolocation defined by Google Maps
    # custom mapping to transform into date shuold be implemented
    item['relative_date'] = relative_date

    # store datetime of scraping and apply further processing to calculate
    # correct date as retrieval_date - time(relative_date)
    item['retrieval_date'] = datetime.now()
    item['rating'] = rating
    item['username'] = username
    item['n_review_user'] = n_reviews
    item['n_photo_user'] = n_photos
    item['url_user'] = user_url

    return item


def filter_string(str):
    strOut = str.replace('\r', ' ').replace('\n', ' ').replace('\t', ' ')
    return strOut


HEADER = ['id_review', 'caption', 'timestamp', 'rating', 'username', 'n_review_user', 'n_photo_user', 'url_user']


def csv_writer(path='data/', outfile='gm_reviews.csv'):
    targetfile = open(path + outfile, mode='w', encoding='utf-8', newline='\n')
    writer = csv.writer(targetfile, quoting=csv.QUOTE_MINIMAL)
    writer.writerow(HEADER)

    return writer


if __name__ == '__main__':

    # store reviews in CSV file
    writer = csv_writer()

    n = 0
    while n < 260:
        reviews = get_reviews(n)

        for r in reviews:
            writer.writerow(list(r.values()))

        n += len(reviews)
