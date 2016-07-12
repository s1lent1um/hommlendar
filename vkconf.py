#!/usr/bin/env python
# -*- coding: utf-8 -*-
from google.appengine.api import mail
import datetime


class AdminNotifier:
    def __init__(self, email):
        self.email = email

    def send_email(self, subject, message):
        letter = mail.EmailMessage()
        letter.sender = u"Hommlendar Bot <%s>" % self.email
        letter.to = self.email

        date = datetime.datetime.now()
        letter.subject = u"Хоммлендарь за %02d.%02d.%04d" % (date.day, date.month, date.year)
        letter.html = """<html><head></head><body>
        <h2>%s</h2>
        %s
        </body></html>""" % (subject, message)
        letter.send()
        return letter.html

    def captcha_notify(self, url):
        message = u"""Хоммлендарь наткнулся на капчу и не может оповестить героев о наступившем дне.<br>
    Помогииите!!! <a href="%s">%s</a>""" % (url, url)
        return self.send_email('Captcha', message)
