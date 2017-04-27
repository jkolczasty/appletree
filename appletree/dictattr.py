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

from collections import OrderedDict


class DictAttrIterator:
    def __init__(self, da):
        self.da = da
        self.keys = da._keys()

    def next(self):
        pass


class DictAttr(object):
    def __init__(self):
        self.__dict__['_attrs'] = OrderedDict()

    def __getattr__(self, name):
        if name in self.__dict__['_attrs']:
            return self.__dict__['_attrs'][name]
        return None

    def __setattr__(self, name, value):
        self.__dict__['_attrs'][name] = value

    def _exists(self, name):
        return name in self.__dict__['_attrs']

    def __getitem__(self, name):
        if name in self.__dict__['_attrs']:
            return self.__dict__['_attrs'][name]
        return None

    def __setitem__(self, name, value):
        self.__dict__['_attrs'][name] = value

    def __delitem__(self, name):
        del self.__dict__['_attrs'][name]

    def _keys(self):
        return self.__dict__['_attrs'].keys()
