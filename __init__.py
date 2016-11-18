#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created with YooLiang Technology (侑良科技).
# Author: Qi-Liang Wen (温啓良）
# Web: http://www.yooliang.com/
# Date: 2015/7/12.
from argeweb import datastore

plugins_helper = {
    "title": u"File",
    "desc": u"File System In Datastore",
    "controllers": {
        "file": {
            "group": u"檔案",
            "actions": [
                {"action": "list", "name": u"檔案管理"},
                {"action": "add", "name": u"新增檔案"},
                {"action": "edit", "name": u"編輯檔案"},
                {"action": "view", "name": u"檢視檔案"},
                {"action": "delete", "name": u"刪除檔案"},
            ]
        },
    }
}
