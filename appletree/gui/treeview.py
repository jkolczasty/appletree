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
from appletree.gui.utils import ObjectCallbackWrapperRef, MakeQAction
from appletree.helpers import T

from appletree.gui.consts import TREE_COLUMN_UID, TREE_COLUMN_NAME, TAGS_NAMES

_CLONE_ITEM = None


class QATTreeWidget(Qt.QTreeWidget):
    # class QATTreeWidget(Qt.QTreeView):
    menu = None

    def __init__(self, win, parent=None):
        super(QATTreeWidget, self).__init__(parent)
        self.setAcceptDrops(True)
        self.win = ref(win)

        self.menu = Qt.QMenu()
        i = 0
        for tag in TAGS_NAMES:
            i += 1
            callback = ObjectCallbackWrapperRef(self, 'on_contextmenu_tag', tag)
            Qt.QShortcut("CTRL+" + str(i), self, member=callback)
            MakeQAction(T("Tag: " + tag), self.menu, callback)

        # TODO: allow plugins to modify context menus
        
        self.menu.addSeparator()
        MakeQAction(T("Copy subtree"), self.menu, self.on_contextmenu_copy)

        self.menupaste = MakeQAction(T("Paste subtree"), self.menu, self.on_contextmenu_paste)
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
        name = item.text(TREE_COLUMN_NAME)
        uid = item.text(TREE_COLUMN_UID)
        _CLONE_ITEM = (projectid, uid, name)

    def on_contextmenu_paste(self):
        global _CLONE_ITEM
        if not _CLONE_ITEM:
            return
        win = self.win()
        if not win:
            return

        items = self.selectedItems()
        if items:
            item = items[0]
            uid = item.text(TREE_COLUMN_UID)
            if uid == _CLONE_ITEM[1]:
                # can not clone to the same place
                return
        else:
            uid = None

        win.cloneDocuments(_CLONE_ITEM[0], _CLONE_ITEM[1], uid)
        _CLONE_ITEM = None

    def on_contextmenu_remove(self):
        win = self.win()
        if not win:
            return

        items = self.selectedItems()
        if not items:
            return
        item = items[0]
        uid = item.text(TREE_COLUMN_UID)

        win.removeDocument(uid)

    def on_contextmenu_tag(self, tag, *args):

        win = self.win()
        if not win:
            return

        items = self.selectedItems()
        if not items:
            return
        item = items[0]
        win.tagDocuemntTree(treeitem=item, toggletags=[tag, ])
