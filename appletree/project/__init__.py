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

import os.path
import logging
from configparser import ConfigParser
from appletree.config import config
from appletree.backend import loadBackend
from appletree.helpers import genuid
import traceback

META_KEYS = ('name', 'backend', 'sync')
PROJECT_DIRS = ('documents', )
PROJECT_DIRS_MODE = 0o0700
# PROJECT_DIRS_MODE = 0o0600


class Project(object):
    def __init__(self, projectid, name, docbackend, syncbackend):
        self.name = name
        self.projectid = projectid
        self.doc = docbackend
        self.sync = syncbackend

    def open(self):  # ???
        return True

    def close(self):
        return True

    def save(self):
        return True

    def sync(self):
        return True


class Projects(object):
    projects = None

    def __init__(self):
        self.log = logging.getLogger("at.projects")
        self.projects = dict()

    def meta(self, projectid):
        if not projectid:
            return None
        try:
            path = os.path.join(config.data_dir, "projects", projectid)
            if not os.path.isdir(path):
                self.log.warn("meta(): no folder: %s", path)
                return None
            cfg = ConfigParser()
            if not cfg.read(os.path.join(path, 'project.conf')):
                self.log.warn("meta(): no project.conf: %s", path)
                return None
            meta = dict()
            meta['name'] = 'Unknown'
            meta['backend'] = 'local'
            meta['sync'] = None

            for k, v in cfg.items('project'):
                if k not in META_KEYS:
                    continue
                meta[k] = v
            return meta
        except Exception as e:
            self.log.error("Failed to retrive project meta: %s: %s: %s", projectid, e.__class__.__name__, e)
            return None

    def open(self, projectid):
        meta = self.meta(projectid)
        if not meta:
            self.log.error("Failed to open project: no meta: %s", projectid)
            return None

        backend = loadBackend(meta.get('backend'), projectid)
        if not backend:
            self.log.error("Failed to open project: unknown backend: %s: %s", projectid, backend)
            return None

        # syncbackend = getSyncBackend(meta.get('sync'))
        syncbackend = None

        project = Project(projectid=projectid, name=meta['name'], docbackend=backend, syncbackend=syncbackend)
        self.projects[projectid] = project

        return project

    def save(self):
        path = os.path.join(config.config_dir, "projects.conf")
        try:
            cfg = ConfigParser()
            section = 'projects'
            cfg.add_section(section)
            projects = self.list()
            cfg.set(section, 'projects', ",".join(projects))
            with open(path, 'w') as f:
                cfg.write(f)
        except Exception as e:
            self.log.error("Failed to save: %s: %s", e.__class__.__name__, e)

    def load(self):
        cfg = ConfigParser()
        path = os.path.join(config.config_dir, "projects.conf")
        try:
            if not cfg.read(path):
                return False

            projects = [s.strip() for s in cfg.get('projects', 'projects').split(",")]

            for projectid in projects:
                self.open(projectid)

        except Exception as e:
            self.log.error("Config read failed: %s: %s", e.__class__.__name__, e)

    def close(self, projectid):
        project = self.projects.get(projectid)
        if not project:
            return
        project.close()

    def list(self):
        return self.projects.keys()

    def create(self, name, docbackend, syncbackend, projectid=None):
        if not projectid:
            projectid = genuid()

        # create project meta

        try:
            path = os.path.join(config.data_dir, "projects", projectid)
            if os.path.isdir(path):
                return None
            os.mkdir(path, mode=PROJECT_DIRS_MODE)
            for folder in PROJECT_DIRS:
                os.mkdir(os.path.join(path, folder), mode=PROJECT_DIRS_MODE)

            cfg = ConfigParser()
            section = 'project'
            cfg.add_section(section)
            cfg.set(section, 'name', name)
            cfg.set(section, 'backend', docbackend)
            cfg.set(section, 'sync', syncbackend or '')

            with open(os.path.join(path, 'project.conf'), 'w') as f:
                cfg.write(f)
            return projectid
        except Exception as e:
            self.log.error("Failed to create project meta: %s: %s: %s", projectid, e.__class__.__name__, e)
            traceback.print_exc()
            return None
