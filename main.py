# -*- coding: utf-8 -*-
import time
import re
import requests

import libs.utils

from bs4 import BeautifulSoup
from libs.pymongodb import pymongodb


class Parser:
    def __init__(self):
        self.ICO_LIST_URL = 'https://icobazaar.com/v2/ico-list'
        self.ICO_LIST_PAGINATION_URL = 'https://icobazaar.com/v2/ico-list?cats%5B%5D={0}&page={1}'
        self.mongo = pymongodb.MongoDB('icobazaar')

    @staticmethod
    def get_html(url):
        time.sleep(2)
        html = requests.get(url).content

        return html

    def get_cats_documents(self):
        return self.mongo.find({}, 'cats_icobazaar')

    def parse_cat(self, documents):
        # One iteration == one category.
        while len(documents) > 0:
            url = documents[0]['link']
            count = 1
            print(url)

            while True:
                time.sleep(2)
                bs = BeautifulSoup(self.get_html(url), 'lxml')

                # Надо собрать один полный документ по одному проекту и сделать сразу запись в бд.

                # * Добавлять данные во временное хранилище вроде vedis.
                # * Добавить логгирование , где будет указано , что данные успешно получены.
                # * Под каждый итем открывать отдельный тред и посмотреть на производительность.
                # ** Попробовать использовать вместо генератора списка генератор словарей , чтобы конце их просто смержить.
                # Get ico full description links.
                ico_full_desc_links = bs.findAll('a', {'class': 'ico-link'})
                ico_full_desc_links = [ico_link['href'] for ico_link in ico_full_desc_links]

                if not ico_full_desc_links:
                    print('page #{} not exist'.format(count))
                    del documents[0]
                    break

                # Get ico logos.
                # * Скачивать по линку и записывать бинарки в файл.
                imgs_src = bs.findAll('div', {'class': 'ico-image'})
                imgs_src = [img_url.find('img')['src'] for img_url in imgs_src]

                # Get ico names.
                ico_names = bs.findAll('h5')
                ico_names = [name.text for name in ico_names]

                # Get updated date.
                updated_dates = bs.findAll('div', {'class': 'campaign_update_widget'})
                updated_dates = [updated_date.find('span').text for updated_date in updated_dates]

                # Get ico short description texts.
                ico_texts = bs.findAll('div', {'class': 'ico-text'})
                ico_texts = [ico_text.text for ico_text in ico_texts]

                # Get ico statuses.
                ico_statuses = bs.findAll('div', {'class': 'ico-condition'})
                ico_statuses = [ico_status.find('div').text for ico_status in ico_statuses]

                # Get ico dates.
                ico_dates = bs.findAll('div', {'class': 'ico-date'})
                ico_dates = [ico_date.text for ico_date in ico_dates]

                # Get ico text ratings.
                ico_text_ratings = bs.findAll('div', {'class': 'ico-eva_class'})
                ico_text_ratings = [ico_text_rating.text for ico_text_rating in ico_text_ratings]

                # Get ico stars ratings.
                ico_stars_ratings = bs.findAll('i', {'class': re.compile('[star] \w{0,4}')})
                ico_stars_ratings = [ico_stars_rating['class'] for ico_stars_rating in ico_stars_ratings]
                ico_stars_ratings = libs.utils.run_rate_transform(ico_stars_ratings)
                print(ico_stars_ratings)

                count += 1
                url = self.ICO_LIST_PAGINATION_URL.format(documents[0]['cat_num'], count)
                print(url)

    def parse_all_cats(self):
        bs = BeautifulSoup(self.get_html(self.ICO_LIST_URL), 'lxml')
        cats = bs.findAll('a', {'class': 'filter-seo-link'})

        data = libs.utils.create_cats_data_list(cats)                       # Create cats data list.

        [self.mongo.insert_one(item, 'cats_icobazaar') for item in data]    # Insert data into db.
        self.mongo.finish()

    def run(self):
        self.parse_all_cats()
        self.parse_cat(self.get_cats_documents())


if __name__ == '__main__':
    Parser().run()


# cProfile.run('main()')
