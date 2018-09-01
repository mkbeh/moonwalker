# -*- coding: utf-8 -*-
import time
import re

import requests

from multiprocessing import Process

from bs4 import BeautifulSoup
from torrequest import TorRequest

from libs.pymongodb import pymongodb
from libs import decorators
from libs import utils


class Parser:
    def __init__(self):
        self.ICO_LIST_URL = 'https://icobazaar.com/v2/ico-list'
        self.ICO_LIST_PAGINATION_URL = 'https://icobazaar.com/v2/ico-list?cats%5B%5D={0}&page={1}'

        self.UPCOMING_URL = 'https://icobazaar.com//v2/ico-list?status%5B0%5D=upcoming&page={}'
        self.ONGOING_URL = 'https://icobazaar.com//v2/ico-list?status%5B0%5D=ongoing&page={}'
        self.ENDED_URL = 'https://icobazaar.com//v2/ico-list?status%5B0%5D=ended&page={}'
        self.SPECIFIC_URLS_LIST = [self.UPCOMING_URL, self.ONGOING_URL, self.ENDED_URL]

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
            html = requests.get(url, timeout=(10, 27), stream=True).content
        except Exception as e:
            print(e)

            with TorRequest(proxy_port=9050, ctrl_port=9051, password=None) as tr:
                tr.reset_identity()
                html = tr.get(url, timeout=(10, 27), stream=True).content

        return html

    def parse_cats(self):
        """
        Method which parse categories urls , titles, add index number and insert them into db.
        :return:
        """
        bs = BeautifulSoup(self.get_html(self.ICO_LIST_URL), 'lxml')
        cats = bs.findAll('a', {'class': 'filter-seo-link'})

        data = utils.create_cats_data_list(cats)                       # Create cats data list.

        [self.mongo.insert_one(item, 'cats_icobazaar') for item in data]    # Insert data into db.
        self.mongo.finish()

    def get_cats_documents(self):
        """
        Method which get categories documents from db and return them.
        :return:
        """
        return self.mongo.find({}, 'cats_icobazaar')

    @staticmethod
    def find_and_write_data(bs_obj, cat_title, count=None):
        """
        Method which find specific data in page and write it into db.
        :param bs_obj:
        :param cat_title:
        :param count:
        :return:
        """
        # Get ico full description links.
        ico_full_desc_links = bs_obj.findAll('a', {'class': 'ico-link'})
        ico_full_desc_links = [ico_link['href'] for ico_link in ico_full_desc_links]

        # Check on clear list.
        if not ico_full_desc_links:
            print('page #{} not exist'.format(count))

            return False

        # Get ico logos.
        imgs_src = bs_obj.findAll('div', {'class': 'ico-image'})
        imgs_src = [img_url.find('img')['src'] for img_url in imgs_src]

        # Get ico names.
        ico_names = bs_obj.findAll('h5')
        ico_names = [name.text for name in ico_names]

        # Get updated date.
        updated_dates = bs_obj.findAll('div', {'class': 'campaign_update_widget'})
        updated_dates = [updated_date.find('span').text for updated_date in updated_dates]

        # Get ico short description texts.
        ico_texts = bs_obj.findAll('div', {'class': 'ico-text'})
        ico_texts = [ico_text.text for ico_text in ico_texts]

        # Get ico statuses.
        ico_statuses = bs_obj.findAll('div', {'class': 'ico-condition'})
        ico_statuses = [ico_status.find('div').text for ico_status in ico_statuses]

        # Get ico dates.
        ico_dates = bs_obj.findAll('div', {'class': 'ico-date'})
        ico_dates = [ico_date.text for ico_date in ico_dates]

        # Get ico text ratings.
        ico_text_ratings = bs_obj.findAll('div', {'class': 'ico-eva_class'})
        ico_text_ratings = [ico_text_rating.text for ico_text_rating in ico_text_ratings]

        # Get ico stars ratings.
        ico_stars_ratings = bs_obj.findAll('i', {'class': re.compile('[star] \w{0,4}')})
        ico_stars_ratings = [ico_stars_rating['class'] for ico_stars_rating in ico_stars_ratings]
        ico_stars_ratings = utils.run_rate_transform(ico_stars_ratings)

        # Clear category title. Change symbols (whitespaces and &) in collections names to _.
        title2 = utils.clear_title(cat_title)

        # Insert data into db.
        mongo = pymongodb.MongoDB('icobazaar')

        for i in range(0, len(ico_full_desc_links)):
            mongo.insert_one({'ico_full_desc_link': ico_full_desc_links[i], 'img_src': imgs_src[i],
                              'ico_name': ico_names[i], 'updated_date': updated_dates[i],
                              'ico_text': ico_texts[i], 'ico_status': ico_statuses[i],
                              'ico_date': ico_dates[i], 'ico_text_rating': ico_text_ratings[i],
                              'ico_star_rating': ico_stars_ratings[i]}, title2)
            mongo.finish()

    def parse(self, cat_url, cat_num, cat_title):
        """
        Method which parse specific category url + pagination pages if they exist and insert parsed data into db.
        :param cat_url:
        :param cat_num:
        :param cat_title:
        :return:
        """
        count = 1

        while True:
            time.sleep(2)
            bs = BeautifulSoup(self.get_html(cat_url), 'lxml')

            if self.find_and_write_data(bs, cat_title, count) is False:
                break

            count += 1
            cat_url = self.ICO_LIST_PAGINATION_URL.format(cat_num, count)

    def parse_cats_data(self, documents):
        """
        Method which parse data for all (exclude cats: ongoing, upcoming, ended) categories and insert them into db.
        :param documents:
        :return:
        """
        # Set links , cats nums, cats titles into lists.
        urls_list = []
        cats_nums = []
        titles_list = []

        for item in documents:
            urls_list.append(item['link'])
            cats_nums.append(item['cat_num'])
            titles_list.append(item['title'])

        # Create processes for parse projects of each category.
        [Process(target=self.parse, args=(url, cat, title)).start()
         for url, cat, title in zip(urls_list, cats_nums, titles_list)]

    def parse_pages_amount(self, url):
        """
        Method which parse pages nums to determine max pages amount of specific category.
        :param url:
        :return:
        """
        html = self.get_html(url.split('&')[0])
        bs = BeautifulSoup(html, 'lxml')

        # Get all pages nums.
        pages_nums = bs.findAll('a', attrs={'class': 'js-filter-page'})
        pages_nums = [int(page_num.text) for page_num in pages_nums if len(page_num) > 0]

        return max(pages_nums)

    def parse_range(self, url, range_):
        for page_num in range_:
            status_name = utils.search_status(url)  # Eject cat status name.

            html = self.get_html(url.format(page_num))   # Get url page num.
            bs = BeautifulSoup(html, 'lxml')

            self.find_and_write_data(bs, status_name)    # Find and write data from page.
            time.sleep(2)

    def parse_specific_ulrs(self, url):
        """
        Method which parse specific url with status ongoing or upcoming or ended.
        :param url:
        :return:
        """
        # Get pages amount.
        pages_amount = self.parse_pages_amount(url)
        time.sleep(2)

        # Get diapasons for pages amount.
        ranges = utils.split_num_by_ranges(pages_amount / 3, pages_amount)

        # Parse every diapason of pages in own process.
        for range_ in ranges:
            Process(target=self.parse_range, args=(url, range_)).start()

    @decorators.log
    def run(self):
        """
        Method which start parsing all ico categories and then data from all categories.
        :return:
        """
        self.mongo.drop_database()                          # Drop db for parse new data.
        self.parse_cats()                                   # Parse all ico categories.
        self.parse_cats_data(self.get_cats_documents())     # Parse data from all categories.

        # Parse specific urls like ...ongoing , ...upcoming, ...ended.
        for url in self.SPECIFIC_URLS_LIST:
            ps = Process(target=self.parse_specific_ulrs, args=(url,))
            ps.start()
            ps.join()

        # Sort collections ended, upcoming, ongoing in mongo.
        utils.sort_col_docs()


if __name__ == '__main__':
    try:
        Parser().run()
    except:
        utils.logger('Success status: %s' % 'ERROR', 'moonwalker.log')
