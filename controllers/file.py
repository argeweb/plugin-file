#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created with YooLiang Technology (侑良科技).
# Author: Qi-Liang Wen (温啓良）
# Web: http://www.yooliang.com/
# Date: 2015/7/12.
import sys
from argeweb import Controller, scaffold, route_menu, route


class File(Controller):
    class Scaffold:
        display_in_list = ['path', 'etag', 'parent_resource', 'display_name', 'content_type', 'content_length', 'data']

    @route_menu(list_name=u'backend', group=u'檔案管理', need_hr=True, text=u'檔案列表', sort=9703)
    def admin_list(self):
        def query_factory_all_without_root(controller):
            return controller.meta.Model.all_without_root()

        self.scaffold.query_factory = query_factory_all_without_root
        return scaffold.list(self)

    @route
    def admin_check(self):
        self.meta.change_view('json')
        path = self.params.get_string('path')
        if path.startswith('/'):
            path = path[1:]
        target = self.meta.Model.get_by_path(path)
        last_md5 = ''
        if target:
            last_md5 = str(target.last_md5)
        self.context['data'] = {'send': self.params.get_string('check_md5') == last_md5 and 'false' or 'true'}

    @staticmethod
    def process_path(path):
        path = path.replace('\\', '/')
        if path.startswith('/') is True:
            path = path[1:]
        return path

    @route
    def admin_upload(self):
        self.meta.change_view('json')
        raw_file = self.request.POST['file']
        path = self.params.get_string('path')
        target_name = self.process_path(path)
        last_md5 = self.params.get_string('check_md5')
        try:
            target = self.meta.Model.get_or_create(target_name, raw_file.type)
            if last_md5 == target.last_md5:
                self.context['data'] = {'error': 'No need to change'}
                return
            if target.resource_data is None:
                from ..models.file_model import FileDataModel
                data = FileDataModel(blob=raw_file.value)
                data.title = path
                data.name = path
            else:
                data = target.resource_data.get()
            data.put()
            target.content_length = raw_file.bufsize
            target.content_type = raw_file.type
            target.path = target_name
            target.etag = last_md5
            target.resource_data = data.key
            target.last_md5 = last_md5
            target.put()
            target.make_directory()
        except:
            self.context['data'] = {'error': sys.exc_info()[0]}
            return
        self.context['data'] = {'info': 'done'}
