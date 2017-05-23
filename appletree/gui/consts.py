#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

from __future__ import absolute_import
from __future__ import print_function

from appletree.gui.qt import Qt, QtCore

# __author__ = 'Jakub Kolasa <jakub@arker.pl'>

TREE_ITEM_FLAGS = QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsDropEnabled
TREE_COLUMN_NAME = 0
TREE_COLUMN_UID = 1
TREE_COLUMN_ICON = 2
TREE_COLUMN_TAGS = 3
TREE_COLUMN_COUNT = 4

TREE_COLUMN_ICON_WIDTH = 32
