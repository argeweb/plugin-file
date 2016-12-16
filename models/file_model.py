#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created with YooLiang Technology (侑良科技).
# Author: Qi-Liang Wen (温啓良）
# Web: http://www.yooliang.com/
# Date: 2015/7/12.

from argeweb import BasicModel
from argeweb import Fields
from urllib import pathname2url
from google.appengine.ext import ndb
from xml.etree import ElementTree as ET
import mimetypes
import logging
import os
from file_self_referential_model import FileModel as selfReferentialModel


def get_file(path):
    return FileModel.get_by_path(path)


class FileDataModel(ndb.Model):
    name = ndb.StringProperty()
    title = ndb.StringProperty()
    blob = ndb.BlobProperty()


class FileModel(BasicModel):
    class Meta:
        label_name = {
            'title': u'顯示名稱',
            'display_name': u'顯示名稱',
            'children': u'子項目',
            'path_as_url': u'URL'
        }
    name = Fields.StringProperty(verbose_name=u'名稱')
    path = Fields.StringProperty(verbose_name=u'檔案路徑')
    content_length = Fields.IntegerProperty(default=0, verbose_name=u'檔案大小')
    content_type = Fields.StringProperty(default='blob', verbose_name=u'檔案類型')
    content_language = Fields.StringProperty(verbose_name=u'語系')
    parent_resource = Fields.CategoryProperty(kind=selfReferentialModel, verbose_name=u'所屬目錄')
    is_collection = Fields.BooleanProperty(default=False, verbose_name=u'是否為目錄')
    is_root = Fields.BooleanProperty(default=False, verbose_name=u'是否為根目錄')
    created = Fields.DateTimeProperty(auto_now_add=True)
    modified = Fields.DateTimeProperty(auto_now=True)
    etag = Fields.StringProperty(verbose_name=u'ETag')
    resource_data = Fields.CategoryProperty(kind=FileDataModel, verbose_name=u'檔案實體')
    last_version = Fields.IntegerProperty(default=0, verbose_name=u'最新的版本')
    last_md5 = Fields.StringProperty(default=u'', verbose_name=u'MD5')
    file = Fields.BlobKeyProperty(verbose_name=u'BlobKey')
    theme = Fields.StringProperty(default=u'', verbose_name=u'所屬樣式')

    @property
    def children(self):
        if self.is_collection:
            logging.info(self.key)
            return FileModel().all().filter(FileModel.parent_resource == self.key)
        else:
            return []

    @property
    def title(self):
        return self.name

    @property
    def display_name(self):
        return os.path.basename('%s' % self.path)

    @property
    def path_as_url(self):
        return pathname2url(self.path)

    @property
    def content_type_or_default(self):
        if self.is_collection:
            return 'httpd/unix-directory'
        else:
            mimetype = mimetypes.guess_type(self.path, strict=False)[0]
            return mimetype if mimetype else 'application/octet-stream'

    @classmethod
    def all_without_root(cls):
        return cls.query(cls.is_root == False).order(-cls.sort)

    @classmethod
    def code_files(cls):
        return cls.query(
                cls.content_type.IN(['css', 'js', 'javascript', 'html', 'text/css', 'text/html', 'text/javascript']),
        ).order(-cls.sort, -cls.key)

    def make_directory(self):
        path = self.path
        if path[0:1] is u'/':
            path = u'/' + path
        paths = path.split('/')
        last_parent = FileModel.root()
        for i in xrange(1, len(paths)):
            path_str = u'/'.join(paths[:i])
            collection = FileModel.get_by_path(path_str)
            if collection is None:
                collection = FileModel()
            collection.name = paths[i]
            collection.path = path_str
            collection.parent_resource = last_parent.key
            collection.is_collection = True
            collection.put()
            last_parent = collection
        self.parent_resource = last_parent.key
        self.put()

    @classmethod
    def root(cls):
        root = cls.all().filter(cls.is_root==True).get()
        if not root:
            root = cls(path='', is_collection=True)
            root.name = '-Root-'
            root.is_root = True
            root.put()
        return root

    @classmethod
    def all_by_path(cls, path=''):
        query = cls.all().filter(cls.path == path + '%')
        return query

    @classmethod
    def get_by_path(cls, path=None):
        return cls.all().filter(cls.path == path).get() if path else cls.root()

    @classmethod
    def exists_with_path(cls, path='', is_collection=None):
        query = cls.all().filter(cls.path == path)
        if is_collection is not None:
            query = query.filter(cls.is_collection == True)
        return query.get(keys_only=True) is not None

    @classmethod
    def content_type_sort_by_name(cls, content_type):
        """ get record with content-type and sort by title """
        return cls.query(cls.content_type == content_type).order(cls.name)

    @classmethod
    def get_or_create(cls, path, content_type):
        n = cls.get_by_path(path)
        if n is None:
            n = cls()
            n.name = os.path.basename('%s' % path)
            n.path = path
            n.content_type = content_type
            n.put()
        return n

    def move_to_path(self, destination_path):
        """Moves this resource and all its children (if applicable) to a new path.
           Assumes that the new path is free and clear."""

        if self.is_collection:
            for child in self.children:
                child_name = os.path.basename(child.path)
                child_path = os.path.join(destination_path,child_name)
                child.move_to_path(child_path)

        self.path = destination_path
        self.put()

    def put(self):
        # workaround for general non-solveable issue of no UNIQUE constraint concept in app engine datastore.
        # anytime we save, we look for the possibility of other duplicate Resources with the same path and delete them.

        try:
            for duped_resource in FileModel.all().filter(FileModel.path == self.path):
                if self.key().id() != duped_resource.key().id():
                    logging.info('Deleting duplicate resource %s with path %s.' % (duped_resource,duped_resource.path))
                    duped_resource.delete()
            if self.name != '-Root-':
                self.name = self.display_name
        except:
            pass
        paths = self.path.split('/')
        theme = ''
        if len(paths) >= 2 and paths[0] == 'themes':
            theme = paths[1]
        self.theme = theme
        super(FileModel, self).put()

    def delete(self):
        """Override delete to delete our associated ResourceData entity automatically."""
        if self.resource_data:
            n = self.resource_data.get()
            if n:
                n.key.delete()
        if self.last_version > 0:
            try:
                from plugins.code.models.code_model import CodeModel
                CodeModel.delete_with_target(self.key)
            except:
                pass
        self.key.delete()

    def delete_recursive(self):
        """Deletes this entity plus all of its children and other descendants."""
        if self.is_collection:
            for child in self.children:
                child.delete_recursive()
        self.delete()

    def export_response(self, href=None):
        datetime_format = '%Y-%m-%dT%H:%M:%SZ'

        response = ET.Element('D:response',{'xmlns:D':'DAV:'})
        ET.SubElement(response, 'D:href').text = href
        propstat = ET.SubElement(response,'D:propstat')
        prop = ET.SubElement(propstat,'D:prop')

        if self.created:
            ET.SubElement(prop, 'D:creationdate').text = self.created.strftime(datetime_format)

        ET.SubElement(prop, 'D:displayname').text = self.display_name

        if self.content_language:
            ET.SubElement(prop, 'D:getcontentlanguage').text = str(self.content_language)

        ET.SubElement(prop, 'D:getcontentlength').text = str(self.content_length)
        ET.SubElement(prop, 'D:getcontenttype').text = str(self.content_type_or_default)

        if self.modified:
            ET.SubElement(prop, 'D:getlastmodified').text = self.modified.strftime(datetime_format)

        resourcetype = ET.SubElement(prop,'D:resourcetype')

        if self.is_collection:
            ET.SubElement(resourcetype, 'D:collection')

        ET.SubElement(propstat,'D:status').text = 'HTTP/1.1 200 OK'
        return response




