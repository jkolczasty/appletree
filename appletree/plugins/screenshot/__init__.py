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
from appletree.plugins.helpers import T
import tempfile
import shlex
import subprocess
import os


class ScreenShotPlugin(ATPlugin):
    friendly_name = "Screenshot Plugin"
    config_defaults = {'screenshot_exec': "spectacle -r -b -d 5000 -n -o {tempfilename}"}

    def initialize(self):
        win = self.win()

    def buildToolbarApplication(self, toolbar):
        toolbar.addWithSeparatorLeft(
            [dict(name='Insert screenshot', icon=self.getIcon('screenshot'), shortcut='CTRL+ALT+S',
                  callback=self.on_toolbar_screenshot),
             ])

    def on_toolbar_screenshot(self, *args):
        try:
            win = self.win()
            if not win:
                return
            docid, editor = win.getCurrentEditor()
            if not docid or not editor or not editor.has_images:
                return
        except:
            pass

        if not self.config.get('screenshot_exec'):
            self.messageDialog(T("Screenshot Plugin"), T("Screenshot tools is not configured. Update preferences."))
            return

        filename = None
        try:
            h, filename = tempfile.mkstemp(prefix='tmpctscreenshot-', suffix='.png')
            os.close(h)
            fargs = dict(tempfilename=filename)
            args = self.config['screenshot_exec'].format(**fargs)
            args = shlex.split(args)
            subprocess.check_call(args)
            if not os.path.getsize(filename):
                os.unlink(filename)
                return
        except Exception as e:
            self.messageDialog(T("Screenshot Plugin"), T("Exception: {0}: {1}".format(e.__class__.__name__, e)))
            if filename:
                os.unlink(filename)
            return

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
