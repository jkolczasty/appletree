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
from appletree.gui.qt import Qt, QtCore
from appletree.gui.mwtoolbar import MainWindowToolbar
from appletree.project import Projects
from appletree.plugins.base import ATPlugins
from appletree.gui.project import ProjectView, NewProjectDialog

TREE_ITEM_FLAGS = QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsDropEnabled


class AppleTreeMainWindow(Qt.QMainWindow):
    ready = False
    plugins = None
    projects = None

    def __init__(self):
        super(AppleTreeMainWindow, self).__init__()

        self.log = logging.getLogger("at")
        self.projects = Projects()
        self.setWindowTitle("AppleTree (Qt " + Qt.QT_VERSION_STR + ")")

        self.menubar = Qt.QMenuBar()
        self.toolbar = MainWindowToolbar(self)

        self.menuplugins = self.menubar.addMenu("Plugins")

        self.plugins = ATPlugins(self)
        self.plugins.discovery()

        self.projects = Projects()
        self.projects.load()
        self.projectsViews = dict()

        # TODO: remove static code, move to dynamic build of toolbars and menus
        self.toolbar.add(
            [dict(name='Add new Project', icon='project-add', shortcut=None, callback=self.on_toolbar_project_add),
             dict(name='Save', icon='save', shortcut='CTRL+S', callback=self.on_toolbar_save),
             dict(name='Add document', icon='document-add', shortcut='CTRL+SHIFT++',
                  callback=self.on_toolbar_document_add),
             ])

        self.toolbar.addWithSeparatorLeft(
            [dict(name='Bold', icon='bold', shortcut='CTRL+B', callback=self.on_toolbar_bold),
             ])

        self.toolbar.addWithSeparatorLeft(
            [
                dict(name='Insert image', icon='image-insert', shortcut='CTRL+SHIFT+I',
                     callback=self.on_toolbar_insert_image),
            ])

        self.setGeometry(50, 50, 1440, 800)
        box = Qt.QVBoxLayout()
        centralwidget = Qt.QWidget()
        centralwidget.setLayout(box)

        self.tabs = Qt.QTabWidget()
        self.tabs.setTabsClosable(True)
        # tabs.tabCloseRequested.connect(self.on_tab_close_req)
        # tabs.currentChanged.connect(self.on_tab_current_changed)

        box.addWidget(self.toolbar)
        box.addWidget(self.tabs)

        self.setCentralWidget(centralwidget)
        self.setMenuBar(self.menubar)

        self.plugins.initialize()
        self.ready = True
        self.treeready = False
        projectslist = self.projects.list()

        for projectid in projectslist:
            self.projectOpen(projectid)

    def projectOpen(self, projectid):
        self.log.info("projectOpen(): %s", projectid)
        idx = self.tabFind(projectid)
        if idx is not None:
            self.tabs.setCurrentIndex(idx)
            return

        project = self.projects.open(projectid)
        if project is None:
            return None

        projectv = ProjectView(project, self)
        projectv.loadDocumentsTree()
        self.tabs.addTab(projectv, project.name)
        self.projectsViews[projectid] = projectv
        self.projects.save()
        return True

    def projectCreate(self, name, docbackend, syncbackend, projectid=None):
        return self.projects.create(name, docbackend, syncbackend, projectid=projectid)

    def on_toolbar_bold(self):
        projectid, projectv = self.getCurrentProject()
        if not projectid:
            self.log.warn("on_toolbar_bold(): No project selected")
            return

        projectv.on_toolbar_bold()

    def getCurrentProject(self):
        index = self.tabs.currentIndex()
        tab = self.tabs.widget(index)
        if not tab:
            return None, None
        projectid = tab.accessibleName()
        projectv = self.projectsViews.get(projectid)
        return projectid, projectv

    def getCurrentEditor(self):
        projectid, projectv = self.getCurrentProject()
        if not projectid:
            return None

        return projectv.getCurrentEditor()

    def tabFind(self, uid):
        for i in range(0, self.tabs.count()):
            tab = self.tabs.widget(i)
            if tab.accessibleName() == uid:
                return i

    def tabSetLabel(self, uid, label):
        idx = self.tabFind(uid)
        if idx is None:
            return

        self.tabs.setTabText(idx, label)

    def save(self, *args):
        pass

    def on_toolbar_insert_image(self, *args):
        projectid, projectv = self.getCurrentProject()
        if not projectid:
            self.log.warn("on_toolbar_document_add(): no current project")
            return None

        projectv.on_toolbar_insert_image()

    def on_toolbar_test(self, *args):
        pass

    def on_toolbar_project_add(self, *args):
        dialog = NewProjectDialog(self)
        if not dialog.exec_():
            return

        name = dialog.fields.get('name')
        backend = 'local'
        sync = None
        if not name:
            return

        projectid = self.projectCreate(name, backend, sync)
        if projectid:
            self.projectOpen(projectid)

    def on_toolbar_document_add(self, *args):
        projectid, projectv = self.getCurrentProject()
        if not projectid:
            self.log.warn("on_toolbar_document_add(): no current project")
            return None

        projectv.on_toolbar_document_add()

    def on_toolbar_save(self):
        projectid, projectv = self.getCurrentProject()
        if not projectid:
            self.log.warn("on_toolbar_document_add(): no current project")
            return None

        projectv.on_toolbar_save()
