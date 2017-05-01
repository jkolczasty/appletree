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

from appletree.dynload import moduleLoad
import logging


_backends = {}


def hasBackend(name):
    return name in _backends


def listBackends():
    return _backends.keys()


def registerBackend(name):
    global _backends
    global _backends

    log = logging.getLogger("at.backend")
    modname = "appletree.backend." + name
    mod, err = moduleLoad(modname)
    if err:
        log.error("Failed to register backend: %s: %s", name, err)
        return None

    _backends[name] = mod


def loadBackend(name, projectid):
    global _backends
    log = logging.getLogger("at.backend")
    try:
        backend = _backends.get(name)
        if not backend:
            return None
        backend = backend.create(projectid)
        return backend
    except Exception as e:
        log.error("Failed to init backend: %s: %s: %s", name, e.__class__.__name__, e)
