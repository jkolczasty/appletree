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

import traceback
import sys


DEBUG = 0


def moduleLoad(module):
    #
    # Dynamic plugin/module load with real dynamic support
    # Real dynamic loading is deprecated cause of freezing methods.
    #
    try:
        return sys.modules[module], None
    except KeyError:
        pass

    #try to import in a very classic way first
    try:
        __import__(module)
        mod = sys.modules[module]
        return mod, None
    except Exception as e:
        #print ">>>",e
        if DEBUG:
            traceback.print_exc(100, file=sys.stdout)
        return None, str(e)
