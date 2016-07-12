# -*- coding: utf-8 -*-

import webapp2
from google.appengine.ext.webapp import template
from os import path
from homm import homm_date
from datetime import timedelta
from datetime import datetime
from time import mktime
from email import utils


class HommRSS(webapp2.RequestHandler):

    def get(self):
        today = datetime.now()
        homm_dates = []
        for i in xrange(50):
            date = today - timedelta(i)
            delta = timedelta(seconds=date.second,
                              minutes=date.minute,
                              hours=date.hour-1) 
            date = date - delta
            rfc_date = utils.formatdate(mktime(date.timetuple()))
            homm_dates.append({'text': homm_date(date), 'pubDate': rfc_date})

        template_values = {'entities': homm_dates}
        rss_filepath = path.join(path.dirname(__file__), 'rss.xml')
        output = template.render(rss_filepath, template_values)

        self.response.headers['Cache-Control'] = 'public,max-age=%s' \
            % 86400
        self.response.headers['Content-Type'] = 'application/rss+xml'
        self.response.out.write(output)

app = webapp2.WSGIApplication([
    ('/rss\\.xml', HommRSS)
], debug=True)
