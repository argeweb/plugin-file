#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created with YooLiang Technology (侑良科技).
# Author: Qi-Liang Wen (温啓良）
# Web: http://www.yooliang.com/
# Date: 2015/7/12.
import os.path
from google.appengine.ext.webapp import blobstore_handlers
from argeweb import ViewDatastore, ViewFunction
from google.appengine.ext import blobstore
from google.appengine.ext import webapp
from models.file_model import get_last_version, get_theme_path, version
from argeweb.core import settings

ViewFunction.register(version)
ViewFunction.register(get_last_version)

plugins_helper = {
    'title': u'檔案管理',
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
                {'action': 'plugins_check', 'name': u'啟用停用模組'},
            ]
        },
    }
}


class GetFileHandler(blobstore_handlers.BlobstoreDownloadHandler):
    def get_string(self, key='', default_value=u''):
        if key is '':
            return default_value
        try:
            if key not in self.request.params:
                rv = default_value
            else:
                rv = self.request.get(key)
        except:
            rv = default_value
        if rv is None or rv is '' or rv is u'':
            rv = u''
        return rv

    def get(self, request_path):
        from plugins.file.models.file_model import get_file
        from google.appengine.api import namespace_manager
        host_information, namespace, theme, server_name = settings.get_host_information_item()
        namespace_manager.set_namespace(namespace)
        if self.request.headers.get('If-None-Match'):
            return self.error(304)

        if request_path.startswith('/assets/') or request_path.startswith('assets/'):
            request_path = request_path.replace('/assets/', '').replace('assets/', '')
            resource = get_file(request_path)
        else:
            request_path = get_theme_path(theme, request_path, self.get_string('dir', u'themes'))
            resource = get_file(request_path)
            if resource is None:
                if os.path.exists(request_path):
                    return self.redirect('/%s' % request_path)
                return self.error(404)
        etag = str(request_path) + '||' + str(theme)
        self.response.headers.setdefault('Access-Control-Allow-Origin', '*')
        self.response.headers.setdefault('Access-Control-Allow-Headers', 'Content-Type, Access-Control-Allow-Headers, Authorization, X-Requested-With')
        self.response.headers['Cache-control'] = 'public, max-age=4800'
        self.response.headers['Content-Type'] = resource.content_type_or_default
        self.response.headers['ETag'] = etag

        blob_key = resource.file
        ext = resource.path.split('.')[1]
        if ext in ['jpg', 'jpeg', 'png', 'gif']:
            self.response.headers['Content-Transfer-Encoding'] = 'base64'

        self.response.headers['Cache-Control'] = 'public, max-age=604800'
        self.response.headers['ETag'] = str(blob_key)

        #blob_key = str(urllib.unquote(source_blob_key))
        blob = blobstore.get(blob_key)
        if blob:
            self.response.headers['Content-Type'] = blob.content_type
            self.send_blob(blob, save_as=False)
        else:
            return self.error(404)


getfile = webapp.WSGIApplication([('/(.+)+', GetFileHandler)], debug=False)