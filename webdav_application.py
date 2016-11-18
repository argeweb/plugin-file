#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created with YooLiang Technology (侑良科技).
# Author: Qi-Liang Wen (温啓良）
# Web: http://www.yooliang.com/
# Date: 2016/8/27

from google.appengine.ext import webapp
from google.appengine.api import namespace_manager
from base64 import b64decode
import traceback
import logging
import cgi
import sys
import os
from argeweb.core.settings import get_host_information_item
from plugins.application_user import get_user
from webdav_handler import WebDAVHandler


class WebDAVApplication(object):
    router = None

    def __init__(self, prefix=None, debug=False, handler_cls=WebDAVHandler, router=None):
        """Initializes this application with the given URL mapping.

        Args:
            debug: if true, we send Python stack traces to the browser on errors
        """
        self._debug = debug
        self._handler = handler_cls()
        self._handler.set_prefix(prefix)
        self.router = router

    def __call__(self, environ, start_response):
        """Called by WSGI when a request comes in."""
        request = webapp.Request(environ)
        response = webapp.Response()
        response.headers['DAV'] = '1,2' # These headers seem to be required for some clients.
        response.headers['MS-Author-Via'] = 'DAV'

        try:
            self.handle_request(environ, request, response)
        except Exception, e:
            self.handle_exception(response, e)

        response.wsgi_write(start_response)
        return ['']

    def set_prefix(self, prefix):
        self._handler.set_prefix(prefix)

    def get_credentials(self, request):
        """Extracts and returns the tuple (username,password) from the given request's HTTP Basic 'Authentication' header."""
        auth_header = request.headers.get('Authorization')

        if auth_header:
            (scheme, base64_raw) = auth_header.split(' ')

            if scheme == 'Basic':
                return b64decode(base64_raw).split(':')
        return (None, None)

    def handle_request(self, environ, request, response):
        """ authentication user."""
        from argeweb.core import settings
        (username, password) = self.get_credentials(request)
        host, namespace, theme = settings.get_host_information_item()
        namespace_manager.set_namespace(namespace)
        user = get_user(username, password)
        if user is None:
            logging.info('if user is None:')
            return self.request_authentication(response)
        if "webdav" not in str(host.plugins).split(","):
            logging.info('if "webdav" not in str(host.plugins).split(","):')
            return response.set_status(404, "Not Found")

        method = environ['REQUEST_METHOD']

        self._handler.initialize(request, response)
        handler_method = getattr(self._handler,method.lower())
        handler_method()

    def request_authentication(self, response):
        response.set_status(401, message='Authorization Required')
        response.headers['WWW-Authenticate'] = 'Basic realm="Secure Area"'

    def error(self, response, code):
        response.clear()
        response.set_status(code)

    def handle_exception(self, response, exception):
        """Called if this handler throws an exception during execution.

        The default behavior is to call self.error(500) and print a stack trace
        if self._debug is True.

        Args:
            exception: the exception that was thrown
        """
        self.error(response, 500)
        logging.exception(exception)
        if self._debug:
            lines = ''.join(traceback.format_exception(*sys.exc_info()))
            response.clear()
            response.out.write('<pre>%s</pre>' % (cgi.escape(lines, quote=True)))

web_dav = WebDAVApplication(debug=True, prefix='webdav')
