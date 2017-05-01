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

from __future__ import absolute_import
from __future__ import print_function

import logging
from appletree.backend import listBackends
from appletree.gui.qt import Qt, QtGui, QtCore
from appletree.helpers import genuid, getIcon
from appletree.gui.texteditor import TabEditorText
from appletree.gui.mwtoolbar import MainWindowToolbar
from appletree.gui.treeview import QATTreeWidget
from appletree.project import Projects
from appletree.plugins.base import ATPlugins

TREE_ITEM_FLAGS = QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsDropEnabled


class ProjectView(Qt.QWidget):
    def __init__(self, project, *args):
        super(ProjectView, self).__init__(*args)
        self.setAccessibleName(project.projectid)

        self.project = project

        self.log = logging.getLogger("at.project." + project.projectid)
        self.editors = dict()

        splitter = Qt.QSplitter()
        box = Qt.QVBoxLayout()
        tree = QATTreeWidget(self)

        tabs = Qt.QTabWidget()
        tabs.setTabsClosable(True)
        tabs.tabCloseRequested.connect(self.on_tab_close_req)
        tabs.currentChanged.connect(self.on_tab_current_changed)

        splitter.addWidget(tree)
        splitter.addWidget(tabs)

        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizePolicy(Qt.QSizePolicy.Expanding, Qt.QSizePolicy.Expanding)

        # self.splitter.show()
        # self.tree.show()
        tree.setColumnCount(3)
        tree.setColumnHidden(1, True)
        tree.setColumnHidden(2, True)

        self.setLayout(box)
        box.addWidget(splitter)

        tree.setHeaderHidden(True)
        # tree.setSelectionModel(Qt.QItemSelectionModel.)
        tree.setDragDropMode(Qt.QAbstractItemView.InternalMove)
        tree.setAcceptDrops(True)
        tree.setAutoScroll(True)

        root = tree.invisibleRootItem()
        # self.connect(tree, Qt.SIGNAL("itemSelectionChanged(QTreeWidgetItem*, int)"), self.on_tree_clicked)
        tree.itemSelectionChanged.connect(self.on_tree_item_selection)
        tree.itemChanged.connect(self.on_tree_item_changed)

        self.setGeometry(50, 50, 1440, 800)

        self.tabs = tabs
        self.root = root
        self.tree = tree
        # self.tree.setSortingEnabled(True)
        # self.tree.sortByColumn(0, QtCore.Qt.Qt_)

        self.ready = True
        self.treeready = False

    def _processDocumentsTree(self, docid, docname, items, parent):
        self.addDocumentTree(docid, docname, parent)

        for childdocid, childdocname, childitems in items:
            self._processDocumentsTree(childdocid, childdocname, childitems, docid)

    def loadDocumentsTree(self):
        self.treeready = False

        backend = self.project.doc
        doctree = backend.getDocumentsTree()
        if not doctree:
            self.treeready = True
            return
        for docid, docname, items in doctree:
            self._processDocumentsTree(docid, docname, items, None)

        self.treeready = True

    def _getDocumentTree(self, root):
        tree = []
        for i in range(0, root.childCount()):
            child = root.child(i)
            # name, docbackend, docid
            docname = child.text(0)
            docid = child.text(1)
            tree.append((docid, docname, self._getDocumentTree(child)))

        return tree

    def saveDocumentsTree(self):
        if not self.treeready:
            return

        backend = self.project.doc

        root = self.tree.invisibleRootItem()
        tree = self._getDocumentTree(root)

        backend.setDocumentsTree(tree)

    def on_tree_item_selection(self):
        items = self.tree.selectedItems()
        if not items:
            return
        item = items[0]

        _type = item.text(2)
        if _type != 'D':
            return

        docid = item.text(1)
        if not docid:
            return
        docname = item.text(0)
        print("??? open:", docid, docname)
        self.open(docid, docname)

    def on_tree_item_changed(self, item):
        if not self.treeready:
            return
        self.log.info("on_tree_item_changed()")
        self.saveDocumentsTree()

    def on_tree_drop_event(self, event):
        dropaction = event.dropAction()
        if dropaction != QtCore.Qt.MoveAction:
            event.ignore()
            return True

        source = self.tree.currentItem()
        destination = self.tree.itemAt(event.pos())
        if not destination:
            event.ignore()
            return True

        srcdocbackend = source.text(1)
        dstdocbackend = destination.text(1)
        if srcdocbackend != dstdocbackend:
            event.ignore()
            return True

        return False

    def on_tree_drop_after_event(self):
        if not self.treeready:
            return
        self.log.info("on_tree_drop_after_event()")
        self.saveDocumentsTree()

    def on_tab_close_req(self, index):
        widget = self.tabs.widget(index)
        docid = widget.accessibleName()
        # noinspection PyBroadException
        try:
            del self.editors[docid]
        except:
            pass

        self.tabs.removeTab(index)
        widget.destroy()

        if self.tabs.count() == 0:
            self.tabs.hide()

    def on_tab_current_changed(self, index):
        widget = self.tabs.widget(index)
        if not widget:
            return

        docid = widget.accessibleName()
        self.log.info("on_tab_current_changed(): docid %s", docid)
        treeitem = self._treeFindDocument(docid)
        self.log.info("on_tab_current_changed(): treeitem %s", treeitem)
        if treeitem:
            self.tree.setCurrentItem(treeitem)

    def on_toolbar_bold(self):
        docid, editor = self.getCurrentEditor()

        if not editor:
            return
        if editor.editor.fontWeight() == QtGui.QFont.Bold:
            editor.editor.setFontWeight(QtGui.QFont.Normal)
        else:
            editor.editor.setFontWeight(QtGui.QFont.Bold)

    def _treeFindDocument(self, docid):
        items = self.tree.findItems(docid, QtCore.Qt.MatchFixedString | QtCore.Qt.MatchRecursive, 1)
        if items:
            return items[0]

        return None

    def addDocumentTree(self, docid, name, parent):
        if parent:
            # TODO: find parent in tree
            parent = self._treeFindDocument(parent)
        else:
            parent = self.tree.invisibleRootItem()

        item = Qt.QTreeWidgetItem(parent, [name, docid, "D"])
        item.setIcon(0, getIcon("doc"))
        item.setExpanded(True)
        item.setFlags(TREE_ITEM_FLAGS)
        return item

    def getCurrentEditor(self):
        index = self.tabs.currentIndex()
        tab = self.tabs.widget(index)
        if not tab:
            return None, None
        docid = tab.accessibleName()
        editor = self.editors.get(docid)
        return docid, editor

    def tabFind(self, uid):
        for i in range(0, self.tabs.count()):
            tab = self.tabs.widget(i)
            if tab.accessibleName() == uid:
                return i

    def open(self, docid, name):
        idx = self.tabFind(docid)
        if idx is not None:
            self.tabs.setCurrentIndex(idx)
            return

        tabeditor = TabEditorText(self, self.project, docid, name)
        self.editors[docid] = tabeditor
        self.tabs.addTab(tabeditor, name)
        c = self.tabs.count()
        if self.tabs.count() == 1:
            self.tabs.show()

        self.tabs.setCurrentIndex(c - 1)

    def tabSetLabel(self, uid, label):
        idx = self.tabFind(uid)
        if idx is None:
            return

        self.tabs.setTabText(idx, label)

    def save(self, *args):
        docid, editor = self.getCurrentEditor()
        self.log.info("save(): %s", docid)

        if not editor:
            # TODO: notify about desync/fail?
            return None

        body = editor.getBody()

        images = editor.getImages()
        # save images
        imagesnames = []
        for res in images:
            imagesnames.append(res)
            url = Qt.QUrl()
            url.setUrl(res)
            resobj = editor.doc.resource(Qt.QTextDocument.ImageResource, url)
            self.project.doc.putImage(docid, res, resobj)

        self.project.doc.putDocumentBody(docid, body)
        self.project.doc.clearImagesOld(docid, imagesnames)
        editor.setModified(False)

    # on_ below are passed from mw to current project

    def on_toolbar_bold(self):
        docid, editor = self.getCurrentEditor()

        if not editor:
            return
        if editor.editor.fontWeight() == QtGui.QFont.Bold:
            editor.editor.setFontWeight(QtGui.QFont.Normal)
        else:
            editor.editor.setFontWeight(QtGui.QFont.Bold)
        pass

    def on_toolbar_insert_image(self, *args):
        docid, editor = self.getCurrentEditor()

        dialog = Qt.QFileDialog()
        dialog.setFileMode(Qt.QFileDialog.AnyFile)
        dialog.setNameFilters(["Images JPEG/PNG/TIFF (*.png *.jpg *.jpeg *.tiff)", ])

        if not dialog.exec_():
            return

        filenames = dialog.selectedFiles()

        for fn in filenames:
            uid = genuid()
            editor.insertImage(uid, fn)

    def on_toolbar_test(self, *args):
        pass

    def on_toolbar_document_add(self, *args):
        currentitem = self.tree.currentItem() or self.tree.invisibleRootItem()
        if not currentitem:
            return

        parent = currentitem.text(1)
        name, ok = Qt.QInputDialog.getText(self, 'New document', 'Enter new document name:')
        if not ok:
            return
        backend = self.project.doc
        docid = genuid()
        if not backend.putDocumentBody(docid, ""):
            self.log.error("Failed to push document to backend")
            return
        self.addDocumentTree(docid, name, parent)
        self.saveDocumentsTree()


    def on_toolbar_save(self):
        self.save()
