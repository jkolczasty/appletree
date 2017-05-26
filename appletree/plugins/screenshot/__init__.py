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

from appletree.plugins.base import ATPlugin
from appletree.helpers import T
from appletree.gui.qt import QtCore
import tempfile
import shlex
import subprocess
import os
from weakref import ref


class ScreenShotPlugin(ATPlugin):
    friendly_name = "Screenshot Plugin"
    config_defaults = {'screenshot_exec': "spectacle -r -b -d 5000 -n -o {tempfilename}"}

    def buildToolbarEditor(self, editor, toolbar):
        if not editor.has_images:
            return

        toolbar.addButtonObjectAction(self, 'screenshot', self.getIcon('screenshot'), desc=T("Insert screenshot"),
                                      shortcut='CTRL+ALT+S', args=[ref(editor)])

    def on_toolbar_action(self, action, *args):
        if action == 'screenshot':
            return self.on_toolbar_screenshot(*args)

    def on_toolbar_screenshot(self, editorref, *args):
        editor = editorref()
        if not editor:
            return

        if not self.config.get('screenshot_exec'):
            self.messageDialog(T("Screenshot Plugin"), T("Screenshot tools is not configured. Update preferences."))
            return

        filename = None
        win = self.win()
        try:
            h, filename = tempfile.mkstemp(prefix='tmpctscreenshot-', suffix='.png')
            os.close(h)
            fargs = dict(tempfilename=filename)
            args = self.config['screenshot_exec'].format(**fargs)
            args = shlex.split(args)
            if win:
                win.setWindowState(QtCore.Qt.WindowMinimized)

            subprocess.check_call(args)
            if not os.path.getsize(filename):
                os.unlink(filename)
                return
        except Exception as e:
            self.messageDialog(T("Screenshot Plugin"), T("Exception: {0}: {1}".format(e.__class__.__name__, e)))
            if filename:
                os.unlink(filename)
            return
        finally:
            if win:
                win.setWindowState(QtCore.Qt.WindowActive)

        try:
            editor.insertImage(filename)
        except Exception as e:
            self.log.error("Exception: %s: %s", e.__class__.__name__, e)
            self.messageDialog(T("Screenshot Plugin"), T("Image Format Not Recognized"))
        finally:
            if filename:
                os.unlink(filename)

    def on_plugin_menu(self):
        dialog = self.preferencesDialog("Screenshot Plugin", "Screenshot Plugin Preferences")

        dialog.addSimpleInput("screenshot_exec", "Screenshot grubber exec", self.config['screenshot_exec'])
        if not dialog.exec_():
            return
        self.config['screenshot_exec'] = dialog.fields['screenshot_exec'].value
        self.configSave()


FACTORY = ScreenShotPlugin
