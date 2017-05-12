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
from weakref import ref
from appletree.gui.qt import Qt, QtCore
from appletree.gui.toolbar import Toolbar
from appletree.helpers import genuid, getIcon, T, messageDialog
from appletree.gui.editor import Editor

from appletree.gui.rteditor import RTEditor
from appletree.gui.pteditor import PTEditor
from appletree.gui.tableeditor import TableEditor

from appletree.gui.treeview import QATTreeWidget

TREE_ITEM_FLAGS = QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsDropEnabled


class ProjectView(Qt.QWidget):
    toolbar = None
    fontselection = None
    fontsizeselection = None

    def __init__(self, win, project, *args):
        super(ProjectView, self).__init__(win, *args)
        self.win = ref(win)
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

        tree.setColumnCount(3)
        tree.setColumnHidden(1, True)
        tree.setColumnHidden(2, True)

        self.setLayout(box)
        self.buildToolbar()

        box.addWidget(self.toolbar)
        box.addWidget(splitter)

        tree.setHeaderHidden(True)
        tree.setDragDropMode(Qt.QAbstractItemView.InternalMove)
        tree.setAcceptDrops(True)
        tree.setAutoScroll(True)

        root = tree.invisibleRootItem()
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

    def buildToolbar(self):
        self.toolbar = Toolbar(self)
        c = len(self.toolbar.children())
        win = self.win()
        if not win:
            return

        win.buildToolbarProject(self, self.toolbar)
        if len(self.toolbar.children()) == c:
            # no items
            self.toolbar.hide()

    def buildToolbarEditor(self, editor, toolbar):
        win = self.win()
        if not win:
            return

        win.buildToolbarEditor(editor, toolbar)

    def isModified(self):
        modified = 0
        for editor in self.editors.values():
            if editor.isModified():
                modified += 1

        return modified

    def closeRequest(self):
        modified = self.isModified()

        if modified:
            if not messageDialog("Close project: unsaved changes",
                                 "You are about close project with unsaved changes. Are you sure?",
                                 details="Unsaved documents: " + str(modified), OkCancel=True):
                return False
        return True

    def close(self):
        self.log.info("Close project")
        super(ProjectView, self).close()
        for editor in self.editors.values():
            editor.close()
            editor.destroy()

        self.editors = {}

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

    def getDocumentTree(self, root=None, docid=None):
        # WARN: changed return value!
        count = 0
        tree = []
        if root is None:
            if docid is None:
                return tree, count
            root = self.treeFindDocument(docid)
            if not root:
                return tree, count
        count = 1
        for i in range(0, root.childCount()):
            child = root.child(i)
            # name, docbackend, docid
            docname = child.text(0)
            docid = child.text(1)
            children, childrencount = self.getDocumentTree(child)
            count += childrencount
            tree.append((docid, docname, children))

        return tree, count

    def saveDocumentsTree(self):
        if not self.treeready:
            return

        backend = self.project.doc

        root = self.tree.invisibleRootItem()
        tree, count = self.getDocumentTree(root)

        backend.setDocumentsTree(tree)

    def treeFindDocument(self, docid):
        items = self.tree.findItems(docid, QtCore.Qt.MatchFixedString | QtCore.Qt.MatchRecursive, 1)
        if items:
            return items[0]

        return None

    def treeRemoveDocument(self, docid):
        items = self.tree.findItems(docid, QtCore.Qt.MatchFixedString | QtCore.Qt.MatchRecursive, 1)
        if items:
            item = items[0]
            for child in item.takeChildren():
                del child
            parent = item.parent()
            if not parent:
                parent = self.tree.invisibleRootItem()
            index = parent.indexOfChild(item)
            parent.takeChild(index)

    def addDocumentTree(self, docid, name, parent):
        if parent:
            # TODO: find parent in tree
            parent = self.treeFindDocument(parent)
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

        meta = self.project.doc.getDocumentMeta(docid)
        _type = meta.get('type') or 'richtext'
        tabeditor = Editor.Editor(_type, self, self.project, docid, name)
        if not tabeditor:
            messageDialog("Unknown document type", "Unknown document type. Could not find suitable editor for it.",
                          details=_type)
            return

        self.editors[docid] = tabeditor
        self.tabs.addTab(tabeditor, name)
        tabeditor.setModified(tabeditor.isModified())

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

        # first getimages, couse this method can change body settings
        images = editor.getImages()
        imageslocal = []
        body = editor.getBody()
        # save images
        for res in images:
            if res.startswith('data:image/'):
                # ignore inline encoded images
                continue
            url = Qt.QUrl()
            url.setUrl(res)
            resobj = editor.doc.resource(Qt.QTextDocument.ImageResource, url)

            localname = self.project.doc.putImage(docid, res, resobj)
            if localname:
                imageslocal.append(localname)

        self.project.doc.putDocumentBody(docid, body)
        self.project.doc.clearImagesOld(docid, imageslocal)
        editor.setModified(False)

    def saveall(self, *args):
        for editor in self.editors.values():
            docid = editor.docid
            if not editor.isModified():
                continue

            self.log.info("save(): %s", docid)
            editor.save()

    def savedrafts(self):
        for editor in self.editors.values():
            docid = editor.docid
            if not editor.isModified():
                continue

            self.log.info("savedrafts(): %s", docid)
            editor.savedraft()

    def _cloneDocuments(self, srcuid, srcname, items, parent, srcprojectv):
        dstuid = genuid()

        docmeta = srcprojectv.project.doc.getDocumentMeta(srcuid)
        docbody = srcprojectv.project.doc.getDocumentBody(srcuid)
        docbodydraft = srcprojectv.project.doc.getDocumentBodyDraft(srcuid)
        images = srcprojectv.project.doc.getImages(srcuid)

        self.project.doc.putDocumentMeta(dstuid, docmeta)
        self.project.doc.putDocumentBody(dstuid, docbody)
        if docbodydraft is not None:
            self.project.doc.putDocumentBodyDraft(dstuid, docbodydraft)

        for image in images:
            __image = srcprojectv.project.doc.getImage(srcuid, image)
            self.project.doc.putImage(dstuid, image, __image)

        self.addDocumentTree(dstuid, srcname, parent)

        for childsrcuid, childsrcname, childitems in items:
            self._cloneDocuments(childsrcuid, childsrcname, childitems, dstuid, srcprojectv)

    def cloneDocuments(self, srcprojectid, srcdocumentid, dstdocumentid):
        """ clone documents from source project:document to this:document"""

        if not self.treeready:
            return

        self.log.info("Clone documents from %s:%s to %s", srcprojectid, srcdocumentid, dstdocumentid)
        win = self.win()
        if not win:
            return

        srcprojectv = win.projectsViews.get(srcprojectid)
        if not srcdocumentid:
            self.log.warn("Can't clone documents, src project is not opened: %s", srcprojectid)
            return

        srcitem = srcprojectv.treeFindDocument(srcdocumentid)
        if not srcitem:
            return
        srcname = srcitem.text(0)

        try:
            self.treeready = False
            # find document subtree (excluding root src document) in src project tree:
            doctree, count = srcprojectv.getDocumentTree(docid=srcdocumentid)

            if not messageDialog("Subtree paste",
                                 "Are you sure you want to paste subtree here?",
                                 details="Subtree elements: {0}".format(count),
                                 OkCancel=True):
                return

            self._cloneDocuments(srcdocumentid, srcname, doctree, dstdocumentid, srcprojectv)
        finally:
            self.treeready = True
        self.saveDocumentsTree()

    def closeTreeTabs(self, docid, items):
        index = self.tabFind(docid)
        if index is not None:
            self.on_tab_close_req(index, ignoreChanges=True)

        for childuid, childname, childitems in items:
            self.closeTreeTabs(childuid, childitems)

    def removeDocuments(self, docid, items):
        for childuid, childname, childitems in items:
            self.removeDocuments(childuid, childitems)

        self.treeRemoveDocument(docid)
        self.project.doc.removeDocument(docid)

    def removeDocument(self, docid):
        if not self.treeready:
            return

        item = self.treeFindDocument(docid)
        if not item:
            return

        name = item.text(0)
        uid = item.text(1)

        # get subtree elements and close tabs if opened before removing documents
        tree, count = self.getDocumentTree(docid=uid)
        if count == 0:
            return

        if not messageDialog("Subtree remove",
                             "Are you sure you want to remove subtree here? This operation is unrecoverable",
                             details="Root document: {0}\nSubtree elements: {1}".format(name, count), OkCancel=True):
            return
        try:
            self.treeready = False
            self.closeTreeTabs(docid, tree)
            self.removeDocuments(docid, tree)
        finally:
            self.treeready = True
            self.saveDocumentsTree()

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
        self.open(docid, docname)

    def on_tree_item_changed(self, item):
        if not self.treeready:
            return
        self.log.info("on_tree_item_changed(): %s")
        name = item.text(0)
        uid = item.text(1)
        if not uid:
            return
        self.tabSetLabel(uid, name)
        self.saveDocumentsTree()

    def on_tree_drop_event(self, event):
        dropaction = event.dropAction()
        if dropaction != QtCore.Qt.MoveAction:
            event.ignore()
            return True

        return False

    def on_tree_drop_after_event(self):
        if not self.treeready:
            return
        self.log.info("on_tree_drop_after_event()")
        self.saveDocumentsTree()

    def on_tab_close_req(self, index, ignoreChanges=False):
        widget = self.tabs.widget(index)
        docid = widget.accessibleName()
        editor = self.editors.get(docid)
        if editor and not ignoreChanges:
            if not editor.closeRequest():
                return

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
        treeitem = self.treeFindDocument(docid)
        if treeitem:
            self.tree.setCurrentItem(treeitem)

    # on_ below are passed from mw to current project

    def on_toolbar_insert_image(self, *args):
        docid, editor = self.getCurrentEditor()
        if not docid or not editor or not editor.has_images:
            return

        dialog = Qt.QFileDialog()
        dialog.setFileMode(Qt.QFileDialog.AnyFile)
        dialog.setNameFilters(["Images JPEG/PNG/TIFF (*.png *.jpg *.jpeg *.tiff)", ])

        if not dialog.exec_():
            return

        filenames = dialog.selectedFiles()

        for fn in filenames:
            editor.insertImage(fn)

    def on_toolbar_test(self, *args):
        doci, editor = self.getCurrentEditor()
        if not editor:
            return

        editor.test()

    def on_toolbar_document_add(self, *args):
        currentitem = self.tree.currentItem() or self.tree.invisibleRootItem()
        if not currentitem:
            return

        parent = currentitem.text(1)
        dialog = NewDocumentDialog(self)
        if not dialog.exec_():
            return

        fields = dialog.fields
        name = fields['name']
        _type = fields['type']

        meta = {'type': _type}

        backend = self.project.doc
        docid = genuid()

        if not backend.putDocumentMeta(docid, meta):
            self.log.error("Failed to push document meta to backend")
            return

        if not backend.putDocumentBody(docid, ""):
            self.log.error("Failed to push document to backend")
            return
        self.addDocumentTree(docid, name, parent)
        self.saveDocumentsTree()

    def on_toolbar_editor_action(self, name, editor, *args):
        if name == 'save':
            return self.save()

        editor.on_toolbar_editor_action(name)


class NewProjectDialog(Qt.QDialog):
    fields = None

    def __init__(self, win):
        super(NewProjectDialog, self).__init__(win)

        self.result = False
        self.fields = dict()

        self.setWindowTitle(T("New project"))
        self.vbox = Qt.QVBoxLayout(self)

        self.box = Qt.QGroupBox(self)
        self.form = Qt.QFormLayout(self.box)

        buttonbox = Qt.QDialogButtonBox()
        buttonbox.setGeometry(Qt.QRect(150, 250, 341, 32))
        buttonbox.setOrientation(QtCore.Qt.Horizontal)
        buttonbox.setStandardButtons(Qt.QDialogButtonBox.Cancel | Qt.QDialogButtonBox.Ok)
        # buttonbox.setWindowTitle(T("New project"))

        self.vbox.addWidget(self.box)
        self.vbox.addWidget(buttonbox)
        self.vbox.setStretch(2, 0)

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        # self.setWindowModality(Qt.Q ApplicationModal)

        buttonbox.accepted.connect(self.on_accept)
        buttonbox.rejected.connect(self.on_reject)
        # QtCore.QMetaObject.connectSlotsByName(Dialog)
        self.adjustSize()
        self.setMinimumWidth(600)
        self.setSizePolicy(Qt.QSizePolicy.MinimumExpanding, Qt.QSizePolicy.MinimumExpanding)

        inputwidget = Qt.QLineEdit()
        inputwidget.textChanged.connect(self.on_changed_name)
        self.form.addRow(T("Project name"), inputwidget)

        inputwidget.setFocus()
        # inputwidget = Qt.QLineEdit()
        # inputwidget.textChanged.connect(self.on_changed_name)
        # self.form.addRow(T("Project name"), inputwidget)

        self.adjustSize()

    def exec_(self):
        super(NewProjectDialog, self).exec_()
        # del self.fields
        return self.result

    def on_accept(self):
        self.result = True
        self.close()

    def on_reject(self):
        self.result = False
        self.close()

    def on_changed_name(self, newtext):
        self.fields['name'] = newtext


class NewDocumentDialog(Qt.QDialog):
    fields = None

    def __init__(self, win):
        super(NewDocumentDialog, self).__init__(win)

        self.result = False
        self.fields = dict()

        self.setWindowTitle(T("New document"))
        self.vbox = Qt.QVBoxLayout(self)

        self.box = Qt.QGroupBox(self)
        self.form = Qt.QFormLayout(self.box)

        buttonbox = Qt.QDialogButtonBox()
        buttonbox.setGeometry(Qt.QRect(150, 250, 341, 32))
        buttonbox.setOrientation(QtCore.Qt.Horizontal)
        buttonbox.setStandardButtons(Qt.QDialogButtonBox.Cancel | Qt.QDialogButtonBox.Ok)
        # buttonbox.setWindowTitle(T("New project"))

        self.vbox.addWidget(self.box)
        self.vbox.addWidget(buttonbox)
        self.vbox.setStretch(2, 0)

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        # self.setWindowModality(Qt.Q ApplicationModal)

        buttonbox.accepted.connect(self.on_accept)
        buttonbox.rejected.connect(self.on_reject)
        # QtCore.QMetaObject.connectSlotsByName(Dialog)
        self.adjustSize()
        self.setMinimumWidth(600)
        self.setSizePolicy(Qt.QSizePolicy.MinimumExpanding, Qt.QSizePolicy.MinimumExpanding)

        inputwidget = Qt.QLineEdit(self)
        inputwidget.textChanged.connect(self.on_changed_name)
        self.form.addRow(T("Document name"), inputwidget)
        inputwidget.setFocus()

        inputwidget = Qt.QComboBox(self)
        inputwidget.addItems(Editor.EditorTypesList())
        inputwidget.currentTextChanged.connect(self.on_changed_type)
        self.fields['type'] = inputwidget.currentText()
        self.form.addRow(T("Document type"), inputwidget)

        self.adjustSize()

    def exec_(self):
        super(NewDocumentDialog, self).exec_()
        # del self.fields
        return self.result

    def on_accept(self):
        self.result = True
        self.close()

    def on_reject(self):
        self.result = False
        self.close()

    def on_changed_name(self, newtext):
        self.fields['name'] = newtext

    def on_changed_type(self, newtype):
        self.fields['type'] = newtype
