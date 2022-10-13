from django.core.paginator import Paginator


def create_paginator(obj_list, page):
    paginator = Paginator(obj_list, 10)
    page_obj = paginator.get_page(page)

    return page_obj
