#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created with YooLiang Technology (侑良科技).
# Author: Qi-Liang Wen (温啓良）
# Web: http://www.yooliang.com/
# Date: 2015/7/12.
from argeweb import datastore
import webapp2
from google.appengine.ext import webapp
from argeweb.core import settings

plugins_helper = {
    'title': u'File',
    'desc': u'File System In Datastore',
    'controllers': {
        'file': {
            'group': u'檔案',
            'actions': [
                {'action': 'list', 'name': u'檔案管理'},
                {'action': 'add', 'name': u'新增檔案'},
                {'action': 'edit', 'name': u'編輯檔案'},
                {'action': 'view', 'name': u'檢視檔案'},
                {'action': 'delete', 'name': u'刪除檔案'},
            ]
        },
    }
}


def get_theme_path(theme, path):
    if path.startswith(u'/themes/%s' % theme) is False:
        path = u'/themes/%s/%s' % (theme, path)
    if path.startswith('/') is True:
        path = path[1:]
    return path


class GetFileHandler(webapp2.RequestHandler):
    def get(self, request_path):
        from plugins.file.models.file_model import get_file
        from google.appengine.api import namespace_manager
        host_information, namespace, theme = settings.get_host_information_item()
        namespace_manager.set_namespace(namespace)
        if request_path.startswith('assets/') is True:
            request_path = request_path[7:]
        else:
            request_path = get_theme_path(theme, request_path)
        if self.request.headers.get('If-None-Match'):
            return self.abort(304)
        resource = get_file(request_path)
        if resource is None:
            return self.abort(404)
        etag = str(request_path) + '||' + str(theme)
        self.response.headers.setdefault('Access-Control-Allow-Origin', '*')
        self.response.headers.setdefault('Access-Control-Allow-Headers', 'Content-Type, Access-Control-Allow-Headers, Authorization, X-Requested-With')
        self.response.headers['Cache-control'] = 'public, max-age=4800'
        self.response.headers['Content-Type'] = resource.content_type_or_default
        self.response.headers['ETag'] = etag
        self.response.out.write(resource.resource_data.get().blob)


getfile = webapp.WSGIApplication([('/(.+)+', GetFileHandler)], debug=False)