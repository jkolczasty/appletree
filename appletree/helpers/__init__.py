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

from uuid import uuid4
import os.path

from appletree.gui.qt import Qt
from appletree.gui.consts import TAGS_NAMES
from appletree.config import config


# dummy translations
def T(*args):
    return args[0]


def genuid():
    return str(uuid4())


def getIcon(name):
    bfn = os.path.join(config.base_dir, "icons", name)
    fn = bfn + ".svg"
    if os.path.isfile(fn):
        return Qt.QIcon(fn)
        fn = bfn + ".png"
    return Qt.QIcon(fn)


def getIconImage(name):
    fn = os.path.join("icons", name + ".png")
    return Qt.QImage(fn)


def getIconPixmap(name):
    bfn = os.path.join(config.base_dir, "icons", name)
    fn = bfn + ".svg"
    if os.path.isfile(fn):
        return Qt.QPixmap(fn, "SVG")

    fn = bfn + ".png"
    return Qt.QPixmap(fn, "PNG")


def messageDialog(title, message, details=None, OkCancel=False, icon=None):
    msg = Qt.QMessageBox()
    if icon:
        msg.setIcon(icon)
    else:
        msg.setIcon(Qt.QMessageBox.Information)

    msg.setText(message)
    msg.setWindowTitle(title)
    if details:
        msg.setDetailedText(details)
    if OkCancel:
        msg.setStandardButtons(Qt.QMessageBox.Ok | Qt.QMessageBox.Cancel)
    else:
        msg.setStandardButtons(Qt.QMessageBox.Ok)

    return msg.exec_() == Qt.QMessageBox.Ok


def tagsSortKey(item):
    try:
        return TAGS_NAMES.index(item)
    except:
        return 9999


def _processDocumentsTreeMeta(project, docid, docname, items, parent, meta, callback):
    callback(project, docid, docname, parent, meta)

    for childdocid, childdocname, childitems in items:
        childmeta = project.doc.getDocumentMeta(childdocid)
        _processDocumentsTreeMeta(project, childdocid, childdocname, childitems, docid, childmeta, callback)


def processProjectDocumentsTreeMeta(project, callback):
    backend = project.doc
    doctree = backend.getDocumentsTree()

    if not doctree:
        return
    for docid, docname, items in doctree:
        meta = project.doc.getDocumentMeta(docid)
        _processDocumentsTreeMeta(project, docid, docname, items, None, meta, callback)


def _processDocumentsTree(project, docid, docname, items, parent, callback):
    callback(project, docid, docname, parent)

    for childdocid, childdocname, childitems in items:
        _processDocumentsTree(project, childdocid, childdocname, childitems, docid, callback)


def processProjectDocumentsTree(project, callback):
    backend = project.doc
    doctree = backend.getDocumentsTree()

    if not doctree:
        return
    for docid, docname, items in doctree:
        _processDocumentsTree(project, docid, docname, items, None, callback)


def _countProjectDocumentsTree(project, docid, docname, parent):
    project.documentsCount += 1


def countProjectDocumentsTree(project):
    project.documentsCount = 0
    processProjectDocumentsTree(project, _countProjectDocumentsTree)
    ret = project.documentsCount
    del project.documentsCount
    return ret


def _listProjectDocumentsTree(project, docid, docname, parent):
    project.documentsList.append(docid)


def listProjectDocumentsTree(project):
    project.documentsList = []
    processProjectDocumentsTree(project, _listProjectDocumentsTree)
    ret = project.documentsList
    del project.documentsList
    return ret
