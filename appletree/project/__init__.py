#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

from __future__ import absolute_import
from __future__ import print_function

# __author__ = 'Jakub Kolasa <jakub@arker.pl'>

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
    def __init__(self, projectid, docbackend, syncbackend):
        self.doc = docbackend
        self.sync = syncbackend
        self.projectid = projectid

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

        project = Project(projectid=projectid, docbackend=backend, syncbackend=syncbackend)
        self.projects[projectid] = project

        return project

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
            return True
        except Exception as e:
            self.log.error("Failed to create project meta: %s: %s: %s", projectid, e.__class__.__name__, e)
            traceback.print_exc()
            return None
