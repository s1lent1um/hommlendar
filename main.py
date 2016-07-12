# -*- coding: utf-8 -*-
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import webapp2
from datetime import date
from os import path
import xml.etree.ElementTree as ET

from homm import homm_date


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


class MainHandler(webapp2.RequestHandler):
    def get(self):
        date_test = ''
        date_parm = self.request.get('date')
        if date_parm:
            try:
                day, month, year = (int(x.strip()) for x in date_parm.split(','))
                date_test = homm_date(date(year, month, day))
            except:
                date_test = ''

        self.response.write(u'Hello underworld!<div>')
        self.response.write(u'%s' % date_test)

        # update_rss(date_test)

app = webapp2.WSGIApplication([
    ('/', MainHandler)
], debug=True)
