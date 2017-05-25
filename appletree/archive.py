#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

from __future__ import absolute_import
from __future__ import print_function

# __author__ = 'Jakub Kolasa <jakub@arker.pl'>

import zipfile
import os.path
import logging
import time
import json

from appletree.helpers import processProjectDocumentsTree


class AppleTreeArchive(object):
    def __init__(self, filename, password=None):
        self.filename = filename
        self.passwd = password
        self.log = logging.getLogger("at.archive")
        self.a = None
        self.mode = 0
        self.meta = dict(projects={}, timestamp=time.time())

    def open(self):
        try:
            self.a = zipfile.ZipFile(self.filename, 'r', compression=zipfile.ZIP_STORED, allowZip64=True)
            self.mode = 0
            self.loadMeta()
            return True
        except Exception as e:
            self.log.error("open(): %s: %s", e.__class__.__name__, e)

    def create(self):
        try:
            self.a = zipfile.ZipFile(self.filename, 'w', compression=zipfile.ZIP_BZIP2, allowZip64=True)
            self.mode = 1
            return True
        except Exception as e:
            self.log.error("create(): %s: %s", e.__class__.__name__, e)

    def close(self):
        ret = True
        if self.mode == 1 and not self.saveMeta():
            ret = False
        self.a.close()
        self.a = None
        return ret

    def loadMeta(self):
        pass

    def saveMeta(self):
        try:
            vpath = 'appletree.archive'
            meta = json.dumps(self.meta)
            self.a.writestr(vpath, meta)
            return True
        except Exception as e:
            self.log.error("saveMeta(): %s: %s", e.__class__.__name__, e)

    def putProject(self, projectid, name):
        self.meta['projects'][projectid] = name

    def putDocumentFile(self, projectid, docid, name, body):
        vpath = os.path.join('projects', projectid, 'documents', docid, name)
        self.a.writestr(vpath, body)

    def putDocument(self, projectid, docid, docmeta, docbody):
        try:
            self.putDocumentFile(projectid, docid, 'document.meta.atdoc', json.dumps(docmeta))
            self.putDocumentFile(projectid, docid, 'document.atdoc', docbody)
            return True
        except Exception as e:
            self.log.error("putDocument(): %s: %s", e.__class__.__name__, e)

    def putDocumentImage(self, projectid, docid, name, data):
        try:
            subpath = os.path.join('resources', 'images', name)
            self.putDocumentFile(projectid, docid, subpath, data)
            return True
        except Exception as e:
            self.log.error("putDocumentImage(): %s: %s", e.__class__.__name__, e)

    def putDocumentTree(self, projectid, doctree):
        try:
            data = json.dumps(doctree)
            vpath = os.path.join('projects', projectid, 'documents', 'applenote.doctree')
            self.a.writestr(vpath, data)
            return True
        except Exception as e:
            self.log.error("putDocumentTree(): %s: %s", e.__class__.__name__)
