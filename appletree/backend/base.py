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

# __author__ = 'Jakub Kolasa <jakub@arker.pl'>

import logging
from hashlib import sha1
import os


class BackendDocuments(object):
    name = "dummy"
    projectid = None

    def __init__(self, projectid):
        self.log = logging.getLogger("at.backend")
        self.projectid = projectid


def resourceNameToLocal(name, ext=""):
    scheme = name.split("://")[0]
    if scheme and scheme in ('http', 'https', 'file'):
        _name = sha1(name.encode('utf-8')).hexdigest() + ext
    else:
        _name = name.rsplit("/", 1)[-1]
        _name = _name.replace(os.sep, "_").replace("..", "__")

    return _name


def resourceImageLocalUrl(projectid, docid, name):
    return '{0}/documents/{1}/resources/images/{2}'.format(projectid, docid, name)
