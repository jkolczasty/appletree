#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

from __future__ import absolute_import
from __future__ import print_function

# __author__ = 'Jakub Kolasa <jakub@arker.pl'>

from weakref import ref
from appletree.gui.qt import Qt


def MakeQAction(name, parent, callback):
    action = Qt.QAction(name, parent)
    action.triggered.connect(callback)
    parent.addAction(action)
    return action


class ObjectCallbackWrapperRef(object):
    def __init__(self, obj, callbackmethod, *args):
        self.obj = ref(obj)
        self.callbackmethod = callbackmethod
        self.args = args

    def __call__(self, *args, **kwargs):
        obj = self.obj()
        if not obj:
            return
        fn = getattr(obj, self.callbackmethod)
        return fn(*self.args, *args, **kwargs)


class CurrentEditorDelegation(object):
    callback = None

    def __init__(self, win, name, callback=None):
        self.win = ref(win)
        self.name = name
        if callback:
            self.callback = callback

    def __call__(self, *args, **kwargs):
        win = self.win()
        if not win:
            return
        docid, editor = win.getCurrentEditor()
        if not editor:
            return

        if self.callback:
            return self.callback(self.name, editor)

        if not editor or not hasattr(editor, self.name):
            return
        fn = getattr(editor, self.name)
        return fn(*args, **kwargs)
