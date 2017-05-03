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

from weakref import ref
from appletree.gui.qt import Qt
from appletree.helpers import T, messageDialog


_CLONE_ITEM = None


class QATTreeWidget(Qt.QTreeWidget):
    menu = None

    def __init__(self, win, parent=None):
        super(QATTreeWidget, self).__init__(parent)
        self.setAcceptDrops(True)
        self.win = ref(win)

        self.menu = Qt.QMenu()

        # TODO: allow plugins to modify context menus
        action = Qt.QAction(T("Copy subtree"), self.menu)
        action.triggered.connect(self.on_contextmenu_copy)
        self.menu.addAction(action)

        action = Qt.QAction(T("Paste subtree"), self.menu)
        action.triggered.connect(self.on_contextmenu_paste)
        action.setDisabled(True)
        self.menupaste = action
        self.menu.addAction(action)
        self.menu.addSeparator()

        action = Qt.QAction(T("Remove subtree"), self.menu)
        action.triggered.connect(self.on_contextmenu_remove)
        self.menu.addAction(action)

    def dropEvent(self, event):
        win = self.win()
        if not win:
            return

        # return if action changed or should be passwd to inherited method
        if win.on_tree_drop_event(event):
            return

        ret = super(QATTreeWidget, self).dropEvent(event)
        win.on_tree_drop_after_event()
        return ret

    def contextMenuEvent(self, event):
        global _CLONE_ITEM

        self.menupaste.setDisabled(_CLONE_ITEM is None)
        self.menu.exec_(event.globalPos())

    def on_contextmenu_copy(self):
        global _CLONE_ITEM
        win = self.win()
        if not win:
            return
        projectid = win.project.projectid
        items = self.selectedItems()
        if not items:
            return
        item = items[0]
        name = item.text(0)
        uid = item.text(1)
        _CLONE_ITEM = (projectid, uid, name)

    def on_contextmenu_paste(self):
        global _CLONE_ITEM
        if not _CLONE_ITEM:
            return
        win = self.win()
        if not win:
            return

        items = self.selectedItems()
        if not items:
            return
        item = items[0]
        uid = item.text(1)
        if uid == _CLONE_ITEM[1]:
            # can not clone to the same place
            return

        if not messageDialog("Subtree paste", "Are you sure you want to paste subtree here? This feature is unstable and can fail. Source: {0}".format(_CLONE_ITEM), OkCancel=True):
            return

        win.cloneDocuments(_CLONE_ITEM[0], _CLONE_ITEM[1], uid)

    def on_contextmenu_remove(self):
        win = self.win()
        if not win:
            return

        items = self.selectedItems()
        if not items:
            return
        item = items[0]
        uid = item.text(1)

        win.removeDocument(uid)
