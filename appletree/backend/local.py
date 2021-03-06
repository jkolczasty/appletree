#!/usr/bin/env python3
#
#       Copyright 2017+ Jakub Kolasa <jkolczasty@gmail.com>
#
#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 3 of the License, or
#       (at your option) any later version.
#
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#
#       You should have received a copy of the GNU General Public License
#       along with this program; if not, write to the Free Software
#       Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#       MA 02110-1301, USA.
#
# __author__ = 'Jakub Kolasa <jkolczasty@gmail.com'>
#

from .base import BackendDocuments, resourceNameToLocal, DOCUMENT_META_KEYS
import os.path
from codecs import encode, decode
import json
from appletree.config import config
from appletree.gui.qt import Qt
import shutil
from configparser import ConfigParser
import traceback


class BackendDocumentsLocal(BackendDocuments):
    name = "local"
    docdir = None

    def __init__(self, projectid):
        super(BackendDocumentsLocal, self).__init__(projectid)
        # TODO: allow to switch between workspaces? Nah.
        self.workdir = os.path.join(config.data_dir)
        self.docdir = os.path.join(self.workdir, "projects", projectid, "documents")

    def getDocumentsTree(self):
        path = os.path.join(self.docdir, "applenote.doctree")
        try:
            with open(path, "r") as f:
                data = json.loads(f.read())
            return data
        except Exception as e:
            self.log.error("getDocumentsTree(): Failed to read meta file: %s: %s", e.__class__.__name__, e)
            return None

    def setDocumentsTree(self, tree):
        path = os.path.join(self.docdir, "applenote.doctree")
        try:
            with open(path, "w") as f:
                f.write(json.dumps(tree))
            return True
        except Exception as e:
            self.log.error("setDocumentsTree(): Failed to read meta file: %s: %s", e.__class__.__name__, e)
            return None

    def getDocumentMeta(self, docid):
        path = os.path.join(self.docdir, docid)

        fn = os.path.join(path, "document.meta.atdoc")
        self.log.info("getDocumentMeta(): %s: %s", docid, fn)
        meta = {}
        try:
            cfg = ConfigParser()
            if not cfg.read(fn):
                return meta

            section = 'document'
            if not cfg.has_section('document'):
                return meta

            for k in DOCUMENT_META_KEYS:
                meta[k] = cfg.get(section, k, fallback=None)
            return meta
        except Exception as e:
            self.log.error("getDocumentMeta(): exception: %s: %s: %s", fn, e.__class__.__name__, e)

        return None

    def putDocumentMeta(self, docid, meta):
        path = os.path.join(self.docdir, docid)

        if not os.path.exists(path) and not self._createDocumentFolder(path):
            return

        fn = os.path.join(path, "document.meta.atdoc")
        self.log.info("putDocumentMeta(): %s: %s", docid, fn)
        try:
            cfg = ConfigParser()
            section = 'document'
            cfg.add_section(section)

            for k, v in meta.items():
                if v is None or k not in DOCUMENT_META_KEYS:
                    continue

                cfg.set(section, k, str(v))
            with open(fn, 'w') as f:
                cfg.write(f)
            return True
        except Exception as e:
            self.log.error("putDocumentMeta(): exception: %s: %s: %s", fn, e.__class__.__name__, e)
            traceback.print_exc()

    def updateDocumentMeta(self, docid, meta):
        _meta = self.getDocumentMeta(docid)
        if not _meta:
            _meta = {}

        _meta.update(meta)
        return self.putDocumentMeta(docid, meta)

    def getDocumentBody(self, docid):
        path = os.path.join(self.docdir, docid)

        fn = os.path.join(path, "document.atdoc")

        self.log.info("getDocumentBody(): %s: %s", docid, fn)
        try:
            if not os.path.isfile(fn):
                return None

            with open(fn, 'rb') as f:
                content = f.read()

            return decode(content, 'utf8')
        except Exception as e:
            self.log.error("getDocumentBody(): exception: %s: %s: %s", fn, e.__class__.__name__, e)

        return None

    def getDocumentBodyDraft(self, docid):
        path = os.path.join(self.docdir, docid)

        fn = os.path.join(path, "document.draft.atdoc")

        self.log.info("getDocumentBodyDraft(): %s: %s", docid, fn)
        try:
            if not os.path.isfile(fn):
                return None

            with open(fn, 'rb') as f:
                content = f.read()

            return decode(content, 'utf8')
        except Exception as e:
            self.log.error("getDocumentBodyDraft(): exception: %s: %s: %s", fn, e.__class__.__name__, e)

        return None

    def dropDocumentBodyDraft(self, docid):
        path = os.path.join(self.docdir, docid)

        fn = os.path.join(path, "document.draft.atdoc")
        if not os.path.isfile(fn):
            return None
        try:
            os.unlink(fn)
        except:
            pass

        self.log.info("dropDocumentBodyDraft(): %s: %s", docid, fn)

    def getImages(self, docid):
        path = os.path.join(self.docdir, docid, "resources", "images")
        ret = []
        # TODO: try...catch
        for fn in os.listdir(path):
            ret.append(fn)

        return ret

    def _createDocumentFolder(self, path):
        try:
            os.mkdir(os.path.join(path))
            os.mkdir(os.path.join(path, "resources"))
            os.mkdir(os.path.join(path, "resources", "images"))
            return True
        except Exception as e:
            self.log.error("_createDocumentFolder(): %s: %s", e.__class__.__name__, e)
            return None

    def putDocumentBody(self, docid, body, dropdraft=True):
        path = os.path.join(self.docdir, docid)

        if not os.path.exists(path) and not self._createDocumentFolder(path):
            return

        fn = os.path.join(path, "document.atdoc")

        self.log.info("putDocumentBody(): %s: %s", docid, fn)
        try:
            with open(fn, 'wb') as f:
                f.write(encode(body, "utf-8"))

            if dropdraft:
                self.dropDocumentBodyDraft(docid)
            return True
        except Exception as e:
            self.log.error("putDocumentBody(): exception: %s: %s: %s", fn, e.__class__.__name__, e)

    def putDocumentBodyDraft(self, docid, body):
        path = os.path.join(self.docdir, docid)

        fn = os.path.join(path, "document.draft.atdoc")
        self.log.info("putDocumentBodyDraft(): %s: %s", docid, fn)
        try:
            with open(fn, 'wb') as f:
                f.write(encode(body, "utf-8"))
            return True
        except Exception as e:
            self.log.error("putDocumentBodyDraft(): exception: %s: %s: %s", fn, e.__class__.__name__, e)

    def removeDocument(self, docid):
        path = os.path.join(self.docdir, docid)

        if not os.path.exists(path):
            return

        self.log.info("removeDocument(): %s: %s", docid, path)
        try:
            shutil.rmtree(path, True)
            return True
        except Exception as e:
            self.log.error("removeDocument(): exception: %s: %s: %s", path, e.__class__.__name__, e)

    def localImageNamePath(self, docid, name):
        return os.path.join(self.docdir, docid, 'resources', 'images', name)

    def getImage(self, docid, name):
        localname = resourceNameToLocal(name, ext='.png')
        path = self.localImageNamePath(docid, localname)

        self.log.info("getImage(): %s: %s: %s", docid, name, path)

        try:
            f = Qt.QFile(path)
            if not f.open(Qt.QFile.ReadOnly):
                self.log.error("getImage(): could not open file: %s", path)
                return None

            data = f.readAll()
            f.close()
            del f

            image = Qt.QPixmap()
            image.loadFromData(data)
            data.clear()
            del data
            return image
        except Exception as e:
            self.log.error("getImage(): exception: %s: %s: %s", path, e.__class__.__name__, e)

        return None

    def getImageRaw(self, docid, name):
        localname = resourceNameToLocal(name, ext='.png')
        path = self.localImageNamePath(docid, localname)

        self.log.info("getImageRaw(): %s: %s: %s", docid, name, path)

        try:
            f = open(path, 'rb')
            data = f.read()
            f.close()
            del f
            return data
        except Exception as e:
            self.log.error("getImageRaw(): exception: %s: %s: %s", path, e.__class__.__name__, e)

        return None

    def putImage(self, docid, name, image):
        localname = resourceNameToLocal(name, ext='.png')
        path = self.localImageNamePath(docid, localname)

        self.log.info("putImage(): %s: %s: %s", docid, name, path)
        try:
            # TODO: support indexed colors formats like GIF?
            image.save(path, "PNG")
            return localname
        except Exception as e:
            self.log.error("putImage(): exception: %s: %s: %s", path, e.__class__.__name__, e)

        return None

    def clearImagesOld(self, docid, currentimages):
        path = os.path.join(self.docdir, docid, "resources", "images")
        self.log.debug("Current images: %s", ", ".join(currentimages))
        for fn in os.listdir(path):
            if fn not in currentimages:
                ffn = os.path.join(path, fn)
                self.log.info("clearImagesOld(): %s", fn)
                os.unlink(ffn)


create = BackendDocumentsLocal
