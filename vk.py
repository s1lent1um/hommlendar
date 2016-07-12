#!/usr/bin/env python
# -*- coding: utf-8 -*-
import webapp2
import webbase
import vkontakte
import homm
import datetime
import urllib, urllib2
import os
from google.appengine.ext import ndb
from google.appengine.ext.webapp import template
from deathbycaptcha import HttpClient as DBCaptchaClient
from vkconf import AdminNotifier

try:
    import json
except ImportError:
    import simplejson as json


class VkToken(ndb.Model):
    """Models an individual Guestbook entry with content and date."""
    str = ndb.StringProperty()
    expires_in = ndb.IntegerProperty()
    user_id = ndb.IntegerProperty()


class VkCaptcha(ndb.Model):
    """Models an individual Guestbook entry with content and date."""
    img = ndb.StringProperty()
    sid = ndb.StringProperty()
    cid = ndb.IntegerProperty()


def redirect_uri():
    return webapp2.uri_for('vk_return', _full=True)


class VkApi(vkontakte.API):
    def __init__(self, timeout=30, *args, **kwargs):
        self.timeout = timeout
        super(VkApi, self).__init__(*args, **kwargs)

    def group_post(self, group_id, message, attachments='', *args, **kwargs):
        self.wall.post(owner_id=-group_id, from_group=1,
                       message=message,
                       attachments=attachments,
                       timeout=self.timeout,
                       *args, **kwargs)
        pass


class VkAuthHandler(webbase.BaseHandler):
    def do_get(self, *args, **kwargs):
        params = dict(
            client_id=self.config['api_id'],
            scope='offline,wall,audio',
            display='popup',
            redirect_uri='http://oauth.vk.com/blank.html',
            response_type='token',
        )

        params = urllib.urlencode(params)

        url = "https://oauth.vk.com/authorize?%s" % params
        path = os.path.join(os.path.dirname(__file__), 'vk_auth.html')
        self.response.out.write(template.render(path, dict(url=url)))


class VkTokenHandler(webbase.BaseHandler):
    def do_get(self):
        # Check 'access_token' in GET parameters
        token = self.request.get('access_token')
        if len(token) == 0:
            self.response.write('No token supplied')
            return

        token = VkToken(
            str=token,
            expires_in=int(self.request.get('expires_in')),
            user_id=int(self.request.get('user_id')),
        )
        token.put()
        self.response.write('Done.')


class VkUpHandler(webbase.BaseHandler):
    def do_get(self, *args, **kwargs):
        """
        @type captcha: VkCaptcha
        """
        date = datetime.datetime.now()
        attached = self.config['audio'][homm.begining_of(date)]

        try:
            token = VkToken().query().fetch(1)[0]
            self.response.write("Token: %s, user Id: %d<br>\n" % (token.str, token.user_id))
        except IndexError:
            self.response.write('No suitable token found')
            return

        try:
            captcha = VkCaptcha().query().fetch(1)[0]
        except IndexError:
            self.response.write("Already posted")
            return

        solver = DBCaptchaClient(self.config['death_by_captcha_login'], self.config['death_by_captcha_password'])
        decoded = solver.get_captcha(captcha.cid)
        if not decoded[u"text"] or not decoded[u"is_correct"]:
            self.response.write("Not decoded yet")
            return

        vk = VkApi(api_id=self.config['api_id'], api_secret=self.config['api_secret'], token=token.str, timeout=30)
        captcha.key.delete()
        mailer = AdminNotifier(self.config['admin_email'])
        try:
            vk.group_post(self.config['group_id'], homm.homm_date(date), attached,
                          captcha_key=decoded[u"text"],
                          captcha_sid=captcha.sid)
            self.response.write('Posted!')
            mailer.send_email(u'Captcha разгадана', "<pre>%s</pre>" % str(decoded))
        except vkontakte.VKError as e:
            if e.code == 14:
                solver.report(decoded[u'captcha'])
                decoding = solver.upload(urllib2.urlopen(e.captcha_img))
                newCaptcha = VkCaptcha(img=e.captcha_img, sid=e.captcha_sid, cid=int(decoding[u'captcha']))
                id = newCaptcha.put()
                mailer.send_email(u'Captcha не разгадана', "<pre>%s</pre><br>\n<pre>%s</pre>" % (str(decoded), str(e)))
            else:
                self.response.write(e)


class VkCreateHandler(webbase.BaseHandler):
    def do_get(self, *args, **kwargs):
        date = datetime.datetime.now()
        attached = self.config['audio'][homm.begining_of(date)]

        try:
            token = VkToken().query().fetch(1)[0]
            self.response.write("Token: %s, user Id: %d<br>\n" % (token.str, token.user_id))
        except IndexError:
            self.response.write('No suitable token found')
            return

        vk = VkApi(api_id=self.config['api_id'], api_secret=self.config['api_secret'], token=token.str, timeout=30)
        try:
            vk.group_post(self.config['group_id'], homm.homm_date(date), attached)
            # vk.captcha.force()
            self.response.write('Posted!')
        except vkontakte.VKError as e:
            mailer = AdminNotifier(self.config['admin_email'])
            if e.code == 20:
                token.key.delete()
                mailer.send_email(u"Token невалиден", "<pre>%s</pre><br>" % str(e))
            if e.code != 14:
                self.response.write(e)
                return

            # send to the solver
            solver = DBCaptchaClient(self.config['death_by_captcha_login'], self.config['death_by_captcha_password'])
            decoding = solver.upload(urllib2.urlopen(e.captcha_img))

            # save to the database to check on it later
            savedCaptcha = VkCaptcha(img=e.captcha_img, sid=e.captcha_sid, cid=int(decoding[u'captcha']))
            id = savedCaptcha.put()

            # report someone
            self.response.write('Captcha sent to the solver')
            mailer.send_email(u"Captcha в обработке", "<pre>%s</pre><br>\n<pre>%s</pre>" % (str(decoding), str(e)))


class VkUpdateHandler(webbase.BaseHandler):
    def do_get(self, *args, **kwargs):
        """
        @type captcha: VkCaptcha
        """
        captcha_id = ""
        try:
            if (self.request.get('captcha_id')) and not self.request.get('captcha_key'):
                id = int(self.request.get('captcha_id'))
                captcha = VkCaptcha.get_by_id(id)
                if captcha:
                    captcha_id = captcha.key.id()
                    raise vkontakte.VKError({
                        'error_code': 14,
                        'error_msg': "Old CAPTCHA",
                        'captcha_img': captcha.img,
                        'captcha_sid': captcha.sid,
                        'request_params': {}
                    })
                else:
                    self.response.write("Already posted")
                    return
            # raise vkontakte.VKError({
            #     'error_code': 14,
            #     'error_msg': "CAPTCHA :-)",
            #     'captcha_img': "http://br-analytics.ru/app/ba_front/img/guest/new/BA-logo.png",
            #     'captcha_sid': "123",
            #     'request_params': {}
            # })
            token = VkToken().query().fetch(1)[0]
            self.response.write("Token: %s, user Id: %d<br>\n" % (token.str, token.user_id))
            vk = vkontakte.API(self.config['api_id'], self.config['api_secret'], token=token.str)
            date = datetime.datetime.now()
            attached = ''
            if date.isoweekday() == 1:
                attached = self.config['audio']['week']
            if date.day == 1:
                attached = self.config['audio']['month']
            if self.request.get('captcha_key'):
                self.response.write('"%s"<br>' % self.request.get('captcha_key'))
                vk.wall.post(owner_id=-self.config['group_id'], from_group=1, message=homm.homm_date(date),
                             attachments=attached, captcha_key=self.request.get('captcha_key'),
                             captcha_sid=self.request.get('captcha_sid'), timeout=30)
                if (self.request.get('captcha_id')):
                    id = int(self.request.get('captcha_id'))
                    captcha = VkCaptcha.get_by_id(id)
                    if captcha:
                        captcha.key.delete()
            else:
                vk.wall.post(owner_id=-self.config['group_id'], from_group=1, message=homm.homm_date(date),
                                 attachments=attached, timeout=30)
            self.response.write('Posted!')
        except IndexError:
            self.response.write('No suitable token found')
        except vkontakte.VKError as e:
            if e.code == 20:
                token.key.delete()
            if e.code == 14:
                if self.request.get('cron'):
                    savedCaptcha = VkCaptcha(img=e.captcha_img, sid=e.captcha_sid)
                    id = savedCaptcha.put()
                    # savedCaptcha.ID
                    path = webapp2.uri_for('vk_update', self.request, captcha_id=id.id())
                    captchaUrl = 'http://' + self.request.host + path
                    mailer = AdminNotifier(self.config['admin_email'])
                    self.response.write(id.id())
                    self.response.write("<br>\n")
                    self.response.write(mailer.captcha_notify(captchaUrl))
                else:
                    self.response.write('''<img src="''' + e.captcha_img + '''"><br>
                    <form method="get">
                    <input type="text" name="captcha_key" value=""><br>
                    <input type="hidden" name="captcha_sid" value="''' + e.captcha_sid + '''"><br>
                    <input type="hidden" name="captcha_id" value="''' + str(captcha_id) + '''"><br>
                    <input type="submit" name="sub" value="Send"><br>
                    </form>
                    ''')
            self.response.write(e)
            self.response.write(e.description)


class VkAudioHandler(webbase.BaseHandler):
    def do_get(self):
        try:
            token = VkToken().query().fetch(1)[0]
            self.response.write("Token: %s, user Id: %d<br>\n" % (token.str, token.user_id))
            vk = vkontakte.API(self.config['api_id'], self.config['api_secret'], token=token.str)
            res = vk.audio.get(gid=43304943, timeout=30)
            self.response.write('<br>')
            if len(res) > 0:
                for audio in res:
                    self.response.write(audio)
                    self.response.write('<br>')
                    self.response.write('<br>')
        except IndexError:
            self.response.write('No suitable token found')
        except vkontakte.VKError as e:
            if e.code == 20:
                token.key.delete()
            self.response.write(e.description)


app = webapp2.WSGIApplication([
    webapp2.Route('/vk_auth', handler=VkAuthHandler, name='vk_auth'),
    webapp2.Route('/vk_return', name='vk_return'),
    webapp2.Route('/vk_audio', handler=VkAudioHandler, name='vk_audio'),
    webapp2.Route('/vk_update', handler=VkUpdateHandler, name='vk_update'),
    webapp2.Route('/vk_up', handler=VkUpHandler, name='vk_up'),
    webapp2.Route('/vk_create', handler=VkCreateHandler, name='vk_create'),
    webapp2.Route('/vk_token', handler=VkTokenHandler, name='vk_token'),
], debug=True)
