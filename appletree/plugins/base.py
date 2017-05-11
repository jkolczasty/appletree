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

from weakref import ref
import os.path
import sys
import re
from appletree.config import config
from configparser import ConfigParser
import traceback
import logging
from appletree.gui.qt import Qt, QtCore
from appletree.plugins.helpers import T

DEBUG = None


class _SignalInputTextChanged(object):
    name = None
    value = None

    def __init__(self, name, value, inputwidget):
        self.name = name
        self.value = value
        self.changed = False
        inputwidget.textChanged.connect(self.on_lineinput_text_changed)

    def on_lineinput_text_changed(self, newtext):
        self.value = newtext
        self.changed = True
        print("NEWTEXT:", self.name, "=", newtext)


class ATPreferencesDialog(Qt.QDialog):
    fields = None

    def __init__(self, win, title, name):
        super(ATPreferencesDialog, self).__init__(win)

        self.fields = {}
        self.result = False

        self.setWindowTitle(title)
        self.vbox = Qt.QVBoxLayout(self)
        self.vbox.addWidget(Qt.QLabel(T(name)))

        self.box = Qt.QGroupBox(self)
        self.form = Qt.QFormLayout(self.box)

        buttonbox = Qt.QDialogButtonBox()
        buttonbox.setGeometry(Qt.QRect(150, 250, 341, 32))
        buttonbox.setOrientation(QtCore.Qt.Horizontal)
        buttonbox.setStandardButtons(Qt.QDialogButtonBox.Cancel | Qt.QDialogButtonBox.Ok)
        buttonbox.setObjectName("buttonBox")
        buttonbox.setWindowTitle(title)

        self.vbox.addWidget(self.box)
        self.vbox.addWidget(buttonbox)
        self.vbox.setStretch(2, 0)

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        # self.setWindowModality(Qt.ApplicationModal)

        buttonbox.accepted.connect(self.on_accept)
        buttonbox.rejected.connect(self.on_reject)
        # QtCore.QMetaObject.connectSlotsByName(Dialog)
        self.adjustSize()
        self.setMinimumWidth(600)
        self.setSizePolicy(Qt.QSizePolicy.MinimumExpanding,Qt.QSizePolicy.MinimumExpanding)

    def addSimpleInput(self, name, label, value):
        inputwidget = Qt.QLineEdit()
        inputwidget.setText(value)
        self.fields[name] = _SignalInputTextChanged(name, value, inputwidget)
        self.form.addRow(label, inputwidget)
        self.adjustSize()

    def exec_(self):
        super(ATPreferencesDialog, self).exec_()
        # del self.fields
        return self.result

    def on_accept(self):
        self.result = True
        self.close()

    def on_reject(self):
        self.result = False
        self.close()


class ATPlugin(object):
    name = None
    friendly_name = None
    config = None
    config_defaults = None
    plugin_menu = None

    def __init__(self, win, plugin_base_path):
        if not self.name:
            self.name = self.__class__.__name__.lower()
        self.base_path = plugin_base_path

        self.log = logging.getLogger("at.plugin." + self.name)
        # self.win = ref(win)
        # NOTE: win is already passed as weakref
        self.win = win
        self.config = {}

        if not self.friendly_name:
            self.friendly_name = self.name

        self.configLoad()

    def configLoad(self):
        self.config = self.config_defaults.copy() if self.config_defaults else dict()
        fn = os.path.join(config.config_dir, self.name + ".conf")
        if not os.path.isfile(fn):
            return

        cfg = ConfigParser()
        try:
            _config = self.config
            cfg.read(fn)
            for name, value in cfg.items(self.name):
                if name not in _config:
                    continue
                try:
                    defvalue = _config[name]
                    if defvalue is not None:
                        value = type(defvalue)(value)
                    _config[name] = value
                except:
                    pass

        except Exception as e:
            self.log.error("Config read failed: %s: %s", e.__class__.__name__, e)

    def configSave(self):
        cfg = ConfigParser()
        try:
            _config = self.config
            section = self.name
            cfg.add_section(section)
            for name, value in _config.items():
                cfg.set(section, name, value)

            fn = os.path.join(config.config_dir, self.name + ".conf")
            with open(fn, 'w') as f:
                cfg.write(f)

        except Exception as e:
            self.log.error("Config write failed: %s: %s", e.__class__.__name__, e)
            traceback.print_exc()

    def getIcon(self, name):
        fn = os.path.join(self.base_path, "icons", name + ".png")
        return Qt.QIcon(fn)

    def preferencesDialog(self, title, name):

        return ATPreferencesDialog(self.win(), title, name)

    def messageDialog(self, title, message, details=None, OkCancel=False):
        msg = Qt.QMessageBox()
        msg.setIcon(Qt.QMessageBox.Information)

        msg.setText(title)
        msg.setInformativeText(message)
        msg.setWindowTitle(title)
        if details:
            msg.setDetailedText(details)
        if OkCancel:
            msg.setStandardButtons(Qt.QMessageBox.Ok | Qt.QMessageBox.Cancel)
        else:
            msg.setStandardButtons(Qt.QMessageBox.Ok)

        return msg.exec_()

    def initialize(self):
        pass

    def on_plugin_menu(self):
        pass

    def buildToolbarEditor(self, editor, toolbar):
        return

    def buildToolbarProject(self, projectv, toolbar):
        return

    def buildToolbarApplication(self, toolbar):
        return


class ATPlugins(object):
    plugins = None
    __iter = 0

    def __init__(self, win):
        self.log = logging.getLogger("at.plugins")
        self.win = ref(win)
        self.plugins = []
        self.debug = config.debug_plugins

    def _load(self, name):
        #
        # Dynamic plugin/module load with real dynamic support
        # Real dynamic loading is deprecated cause of freezing methods.
        #
        module = 'appletree.plugins.{0}'.format(re.sub("[^a-zA-Z0-9_]", "_", name))

        try:
            return sys.modules[module], None
        except KeyError:
            pass

        # try to import in a very classic way first
        try:
            __import__(module)
            mod = sys.modules[module]
            return mod, None
        except Exception as e:
            if self.debug:
                traceback.print_exc(100, file=sys.stdout)
            return None, str(e)

    def load(self, name):
        self.log.info("Load: %s", name)
        mod, err = self._load(name)

        plugin_base_path = os.path.join(config.base_dir, "appletree", "plugins", name)

        obj = mod.FACTORY(self.win, plugin_base_path)
        pname = obj.name
        fname = obj.friendly_name
        self.plugins.append(obj)
        self.log.info("Ready: %s: %s: %s", name, pname, fname)
        win = self.win()
        if not win:
            return

        action = Qt.QAction(fname, win)
        action.setStatusTip("Plugin " + fname)
        action.triggered.connect(obj.on_plugin_menu)
        win.menuplugins.addAction(action)

    def configSave(self):
        for p in self.plugins:
            p.config_save()

    def buildMenus(self):
        for obj in self.plugins:
            obj.build_plugin_menu()

    def discovery(self):
        try:
            plugin_dir = os.path.join(config.base_dir, "appletree", "plugins")
            for fn in os.listdir(plugin_dir):
                try:
                    if fn.startswith("_") or fn.startswith("."):
                        continue

                    ffn = os.path.join(plugin_dir, fn)
                    if not os.path.isdir(ffn):
                        continue

                    self.load(fn)
                except Exception as e:
                    self.log.error("Failed to discover plugin: %s: %s: %s", fn, e.__class__.__name__, e)
        except Exception as e:
            self.log.error("Failed to discover plugins: %s: %s", e.__class__.__name__, e)

    def initialize(self):
        for p in self.plugins:
            try:
                p.initialize()
            except Exception as e:
                self.log.error("Initialize failed: %s: %s: %s", p.name, e.__class__.__name__, e)

    def __iter__(self):
        return iter(self.plugins)


