#!/usr/bin/env python
# -*- coding: utf-8 -*-
import abc
import webapp2
import traceback
import yaml
from vkconf import AdminNotifier


class BaseHandler(webapp2.RequestHandler):
    __metaclass__ = abc.ABCMeta

    def __init__(self, request=None, response=None):
        super(BaseHandler, self).__init__(request=request, response=response)

        # load the configuration yaml file
        stream = file('config.yml', 'r')
        self.config = yaml.load(stream)

    def get(self, *args, **kwargs):
        try:
            self.do_get(*args, **kwargs)
        except Exception as e:
            mailer = AdminNotifier(self.config['admin_email'])
            mailer.send_email(u'Unhandled exception!', "<h3>%s</h3><pre>%s</pre>" % (e.message, traceback.format_exc(e)))
            raise e

    @abc.abstractmethod
    def do_get(self, *args, **kwargs):
        """Method encapsulated in error reporting handler"""
        return
