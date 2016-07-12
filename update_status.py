# -*- coding: utf-8 -*-

import webapp2
# import logging
import tweepy
import homm
import yaml
from os import path
import xml.etree.ElementTree as ET

stream = file('config.yml', 'r')
config = yaml.load(stream)


hommlendar_user_token_str = config['twitter']['hommlendar_token']

auth = tweepy.OAuthHandler(config['twitter']['consumer_key'], config['twitter']['consumer_secret'])
auth.access_token = tweepy.oauth.OAuthToken.from_string(hommlendar_user_token_str)
api = tweepy.API(auth)


PROJECT_DIR = path.dirname(__file__)


def update_rss(date):
    file_path = path.join(PROJECT_DIR, 'rss.xml')
    tree = ET.parse(file_path)
    root = tree.getroot()
    channel = root.find('channel')
    new_item = ET.Element('item')
    new_item.text = date
    # 6 is image tag position after which items are going
    channel.insert(6, new_item)
    root.write(file_path)


class UpdateStatusHandler(webapp2.RequestHandler):
    def get(self):
        global api
        _date = homm.homm_date()
        api.update_status(_date)
        # update_rss(_date)

        self.response.write('You shouldnt be here!')


app = webapp2.WSGIApplication([
    ('/update_status', UpdateStatusHandler)
], debug=True)
