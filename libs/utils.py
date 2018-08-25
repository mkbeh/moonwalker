# -*- coding: utf-8 -*-
import re


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