# -*- coding: utf-8 -*-
import time
import re
import cProfile

from multiprocessing import Process, Queue

import requests
import libs.utils

from bs4 import BeautifulSoup
from libs.pymongodb import pymongodb
from torrequest import TorRequest


class Parser:
    def __init__(self):
        self.ICO_LIST_URL = 'https://icobazaar.com/v2/ico-list'
        self.ICO_LIST_PAGINATION_URL = 'https://icobazaar.com/v2/ico-list?cats%5B%5D={0}&page={1}'
        self.mongo = pymongodb.MongoDB('icobazaar')

    @staticmethod
    def get_html(url):
        """
        Method which send GET request to specific url and return html.
        :param url:
        :return:
        """
        time.sleep(2)

        try:
            html = requests.get(url, timeout=(3.05, 27), stream=True).content
            print(html)
        except Exception as e:
            print(e)

            with TorRequest(proxy_port=9050, ctrl_port=9051, password=None) as tr:
                tr.reset_identity()
                html = tr.get(url, timeout=(3.05, 27), stream=True).content

        return html

    def parse_all_cats(self):
        """
        Method which parse categories urls , titles, add index number and insert them into db.
        :return:
        """
        bs = BeautifulSoup(self.get_html(self.ICO_LIST_URL), 'lxml')
        cats = bs.findAll('a', {'class': 'filter-seo-link'})

        data = libs.utils.create_cats_data_list(cats)                       # Create cats data list.

        [self.mongo.insert_one(item, 'cats_icobazaar') for item in data]    # Insert data into db.
        self.mongo.finish()

    def get_cats_documents(self):
        """
        Method which get categories documents from db and return them.
        :return:
        """
        return self.mongo.find({}, 'cats_icobazaar')

    def parse_cats_data(self, documents):
        """
        Method which parse data for all categories and insert them into db.
        :param documents:
        :return:
        """
        # One iteration == one category.
        while len(documents) > 0:
            url = documents[0]['link']
            count = 1

            while True:
                time.sleep(2)
                bs = BeautifulSoup(self.get_html(url), 'lxml')

                # Get ico full description links.
                ico_full_desc_links = bs.findAll('a', {'class': 'ico-link'})
                ico_full_desc_links = [ico_link['href'] for ico_link in ico_full_desc_links]

                # Check on clear list.
                if not ico_full_desc_links:
                    print('page #{} not exist'.format(count))
                    del documents[0]

                    break

                # Get ico logos.
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

                # Clear category title. Change symbols in collections names (%^* etc) to _.
                title = libs.utils.clear_title(documents[0]['title'])

                # Insert data into db.
                for i in range(0, len(ico_full_desc_links)):
                    self.mongo.insert_one({'ico_full_desc_link': ico_full_desc_links[i], 'img_src': imgs_src[i],
                                           'ico_name': ico_names[i], 'updated_date': updated_dates[i],
                                           'ico_text': ico_texts[i], 'ico_status': ico_statuses[i],
                                           'ico_date': ico_dates[i], 'ico_text_rating': ico_text_ratings[i],
                                           'ico_star_rating': ico_stars_ratings[i]}, title)

                count += 1
                url = self.ICO_LIST_PAGINATION_URL.format(documents[0]['cat_num'], count)

    def run(self):
        """
        Method which start parsing all ico categories and then data from all categories.
        :return:
        """
        self.parse_all_cats()                               # Parse all ico categories.
        self.parse_cats_data(self.get_cats_documents())     # Parse data from all categories.


if __name__ == '__main__':
    # Parser().run()
    cProfile.run('Parser().run()')
