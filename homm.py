# -*- coding: utf-8 -*-
import datetime
__author__ = 'silentium'


def week_num(date):
    first_weekday = (date - datetime.timedelta(date.day - 1)).isoweekday()
    wnum = (date.day + first_weekday - 2) // 7
    # if month starts fom monday, week count starts from 1
    if first_weekday == 1:
        return wnum + 1
    else:
        return wnum


def begining_of(date=None):
    if not date:
        date = datetime.datetime.now()
    if date.isoweekday() == 1:
        return 'week'
    if date.day == 1:
        return 'month'
    return 'day'


def homm_date(date=None):
    if not date:
        date = datetime.datetime.now()
    return u"Месяц: %d, Неделя: %d, День: %d" % (date.month, week_num(date), date.isoweekday())
