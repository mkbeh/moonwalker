# -*- coding: utf-8 -*-
import re

from libs.pymongodb import pymongodb


# Func which converting text rate like ['star', 'full'] into int like 1
def convert_text_rate_into_int(item):
    if item[1] == 'full':
        return 1
    elif item[1] == 'half':
        return 0.5
    elif item[1] == '':
        return 0


# Func which sum list items.
def list_sum(num_list):
    sum_ = 0

    for i in num_list:
        sum_ = sum_ + i

    return sum_


# Func which split list by n elems.
def split_list(lst, n):
    return [lst[i:i + n] for i in range(0, len(lst), n)]


# Transform text rating into integer values list.
def run_rate_transform(ico_stars_ratings):
    int_rate_lst = list(map(convert_text_rate_into_int, ico_stars_ratings))     # transform text into int vals.
    splitted_list = split_list(int_rate_lst, 5)                                 # split list by 5 elems.
    final_lst = list(map(list_sum, splitted_list))                              # sum sub lists values.

    return final_lst


# Func which creating categories data list from bsobj.
def create_cats_data_list(bsobj_cats):
    data = []
    cat_num = 0

    for cat in bsobj_cats:
        cat_num += 1

        if 'upcoming' not in cat['href'] and 'ongoing' not in cat['href'] and 'all' not in cat['href']:
            data.append({'title': cat['title'], 'link': cat['href'], 'cat_num': cat_num})

    return data


# Func which replace whitespaces and & to _.
def clear_title(cat_title):
    pattern = re.compile(r'&')

    try:
        re.search(pattern, cat_title).group()
        return cat_title.replace('&', '_').replace(' ', '')

    except AttributeError:
        return cat_title.replace(' ', '_')


# Func which split range into nums.
def split_range_into_nums(diaposon):
    lst = []
    [lst.append(num) for num in range(diaposon[0], diaposon[1] + 1) if num != 0]

    return lst


# Func which split num by diapasons , like -> 15: (0,2),(3,5)...etc.
def split_num_by_ranges(step, num):
    lst = []

    for i in range(0, round(step)):
        if i * 3 + 2 + 3 < num:
            lst.append((i * 3, i * 3 + 2))

        else:
            lst.append((i * 3, num))
            break

    lst = list(map(split_range_into_nums, lst))

    return lst


# Func which search specific status in url.
def search_status(url):
    pattern = re.compile(r'ended|upcoming|ongoing')
    return re.search(pattern, url).group()


def sort_col_docs():
    collections_names = ['ended', 'upcoming', 'ongoing']

    for col_name in collections_names:
        mongo = pymongodb.MongoDB('icobazaar')
        sorted_docs = mongo.find_with_sort(col_name, 'ico_star_rating')
        mongo.drop_collection(col_name)
        mongo.insert_many(sorted_docs, col_name)
