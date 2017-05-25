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
from configparser import ConfigParser
import os.path
from appletree.config import config
from appletree.gui.qt import Qt, QtCore, APP
from appletree.helpers import getIcon, getIconSvg, messageDialog
from appletree.gui.toolbar import Toolbar
from appletree.gui.utils import ObjectCallbackWrapperRef
from appletree.project import Projects
from appletree.plugins.base import ATPlugins
from appletree.gui.project import ProjectView, NewProjectDialog
from appletree.gui.progressdialog import ProgressDialog
import traceback
import time

TREE_ITEM_FLAGS = QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsDropEnabled


class AppleTreeMainWindow(Qt.QMainWindow):
    ready = False
    plugins = None
    projects = None

    def __init__(self):
        super(AppleTreeMainWindow, self).__init__()
        self.setWindowIcon(getIcon('app'))
        self.log = logging.getLogger("at")
        self.projects = Projects()
        self.setWindowTitle("AppleTree (Qt " + Qt.QT_VERSION_STR + ")")

        self.menubar = Qt.QMenuBar()
        self.toolbar = Toolbar(self)

        self.menuprojects = self.menubar.addMenu("Projects")
        self.menuplugins = self.menubar.addMenu("Plugins")

        self.plugins = ATPlugins(self)
        self.plugins.discovery()

        self.projects = Projects()
        self.projectsViews = dict()

        self.buildToolbar()

        self.setGeometry(50, 50, 1440, 800)
        box = Qt.QVBoxLayout()
        centralwidget = Qt.QWidget()
        centralwidget.setLayout(box)

        self.tabs = Qt.QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.on_tab_close_req)
        # tabs.currentChanged.connect(self.on_tab_current_changed)

        box.addWidget(self.toolbar)
        box.addWidget(self.tabs)

        self.setCentralWidget(centralwidget)
        self.setMenuBar(self.menubar)

        self.plugins.initialize()
        self.ready = True
        self.treeready = False

        self.load()

    def buildToolbar(self):

        # TODO: remove static code, move to dynamic build of toolbars and menus
        self.toolbar.add(
            [dict(name='Save', icon=getIconSvg('document-save'), shortcut='CTRL+S', callback=self.on_toolbar_save),
             dict(name='Save all', icon=getIconSvg('document-save-all'), shortcut=None,
                  callback=self.on_toolbar_saveall),
             dict(name='Add new Project', icon='project-add', shortcut=None, callback=self.on_toolbar_project_add),
             dict(name='Add document', icon='document-add', shortcut='CTRL+SHIFT++',
                  callback=self.on_toolbar_document_add),
             ])

        for p in self.plugins:
            try:
                p.buildToolbarApplication(self.toolbar)
            except Exception as e:
                self.log.error("buildToolbar(): %s: %s", e.__class__.__name__, e)

    def buildToolbarProject(self, projectv, toolbar):
        for p in self.plugins:
            try:
                p.buildToolbarProject(projectv, toolbar)
            except Exception as e:
                self.log.error("buildToolbarProject(): %s: %s", e.__class__.__name__, e)

    def buildToolbarEditor(self, editor, toolbar):
        for p in self.plugins:
            try:
                p.buildToolbarEditor(editor, toolbar)
            except Exception as e:
                self.log.error("buildToolbarEditor(): %s: %s", e.__class__.__name__, e)

    def projectAdd(self, projectid):
        project = self.projects.open(projectid)
        if not project:
            return
        action = Qt.QAction(project.name, self)
        action.triggered.connect(ObjectCallbackWrapperRef(self, 'on_menu_project', projectid))
        self.menuprojects.addAction(action)

    def projectOpen(self, projectid):
        self.log.info("projectOpen(): %s", projectid)
        idx = self.tabFind(projectid)
        if idx is not None:
            self.tabs.setCurrentIndex(idx)
            return

        project = self.projects.open(projectid)
        if project is None:
            return None

        project.active = True
        projectv = ProjectView(self, project)
        projectv.loadDocumentsTree()
        idx = self.tabs.addTab(projectv, project.name)
        self.projectsViews[projectid] = projectv
        self.tabs.setCurrentIndex(idx)
        return True

    def projectCreate(self, name, docbackend, syncbackend, projectid=None):
        return self.projects.create(name, docbackend, syncbackend, projectid=projectid)

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

    def load(self):
        ProgressDialog.create(2, self)

        path = os.path.join(config.config_dir, "appletree.conf")
        try:
            cfg = ConfigParser()
            cfg.read(path)

            section = 'appletree'
            if not cfg.has_section(section):
                return

            activeproject = cfg.get(section, 'activeproject', fallback=None)

            sections = cfg.sections()
            c = len(sections)
            i = 0
            for section in cfg.sections():
                i += 1
                ProgressDialog.progress(i * 100 / c)
                ProgressDialog.yield_()
                active = cfg.get(section, 'active', fallback='0') == '1'
                if not section.startswith('project:'):
                    continue
                projectid = section[8:]

                self.projectAdd(projectid)

                if not active:
                    continue

                if not self.projectOpen(projectid):
                    continue

                view = self.projectsViews.get(projectid)
                if not view:
                    self.log.error("load(): Can't open project view after open: %s", projectid)
                    continue

                openeddocuments = cfg.get(section, 'openeddocuments', fallback="")
                openeddocuments = [s.strip() for s in openeddocuments.split(",") if s]
                activedocument = cfg.get(section, 'activedocument', fallback=None)

                for docid in openeddocuments:
                    ProgressDialog.yield_()
                    view.open(docid)

                if activedocument:
                    view.setCurrentDocument(activedocument)

                if activeproject is not None:
                    index = self.tabFind(activeproject)
                    if index is not None:
                        self.tabs.setCurrentIndex(index)

        except Exception as e:
            self.log.error("Failed to load: %s: %s", e.__class__.__name__, e)
            traceback.print_exc()
        finally:
            ProgressDialog.done()

    def save(self, *args):
        ProgressDialog.create(0, self)
        path = os.path.join(config.config_dir, "appletree.conf")
        try:
            cfg = ConfigParser()

            projects = self.projects.items()
            c = len(projects)
            i = 0
            for projectid, project in projects:
                i += 1

                ProgressDialog.progress(i * 100 / c)
                pv = self.projectsViews.get(projectid)
                active = pv is not None
                section = 'project:{0}'.format(projectid)

                cfg.add_section(section)
                cfg.set(section, 'active', '1' if active else '0')

                if not active:
                    continue

                openeddocuments = []
                for i in range(0, pv.tabs.count()):
                    ProgressDialog.yield_()
                    tab = pv.tabs.widget(i)
                    docid = tab.accessibleName()
                    openeddocuments.append(docid)

                cfg.set(section, 'openeddocuments', ",".join(openeddocuments))
                activedocument = pv.getCurrentDocument()
                if activedocument:
                    cfg.set(section, 'activedocument', activedocument)

            section = 'appletree'
            cfg.add_section(section)
            index = self.tabs.currentIndex()
            projectid = self.tabs.widget(index).accessibleName() if index > -1 else None
            if projectid:
                cfg.set(section, 'activeproject', projectid)

            with open(path, 'w') as f:
                cfg.write(f)
        except Exception as e:
            self.log.error("Failed to save: %s: %s", e.__class__.__name__, e)
            traceback.print_exc()
        finally:
            ProgressDialog.done()

    def closeEvent(self, event):
        for pv in self.projectsViews.values():
            pv.savedrafts()

        event.accept()
        self.save()

    # signals/callbacks

    # project close
    def on_tab_close_req(self, index, ignoreChanges=False):
        widget = self.tabs.widget(index)
        projectid = widget.accessibleName()
        if not projectid:
            return
        project = self.projects.get(projectid)
        projectv = self.projectsViews.get(projectid)
        if not project or not projectv:
            return

        if not ignoreChanges and not projectv.closeRequest():
            return

        del self.projectsViews[projectid]
        projectv.close()
        del projectv
        widget.close()
        project.close()

        self.tabs.removeTab(index)
        widget.destroy()
        project.active = False

    def on_menu_project(self, projectid, *args):
        self.projectOpen(projectid)

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
            self.log.warn("on_toolbar_save(): no current project")
            return None

        projectv.save()

    def on_toolbar_saveall(self):
        for pv in self.projectsViews.values():
            pv.saveall()
