#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created with YooLiang Technology (侑良科技).
# Author: Qi-Liang Wen (温啓良）
# Web: http://www.yooliang.com/
# Date: 2015/7/12.

from argeweb import Controller, scaffold, route_menu, route_with, route
from argeweb.components.pagination import Pagination
from argeweb.components.search import Search
from .. import plugins_helper


class File(Controller):
    class Meta:
        components = (scaffold.Scaffolding, Pagination, Search)
        pagination_actions = ("list",)
        pagination_limit = 50

    class Scaffold:
        helper = plugins_helper
        display_properties_in_list = ("path", "etag", "parent_resource", "display_name", "content_type", "content_length", "data")

    @route_menu(list_name=u"backend", text=u"hr", sort=9711, group=u"檔案管理")
    @route_menu(list_name=u"backend", text=u"檔案列表", sort=9712, group=u"檔案管理")
    def admin_list(self):
        model = self.meta.Model
        def query_factory_all_without_root(self):
            return model.all_without_root()
        self.scaffold.query_factory = query_factory_all_without_root
        return scaffold.list(self)
