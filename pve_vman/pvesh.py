# -*- coding: utf-8 -*-
#
#  Copyright (c) 2017 RobHost GmbH <support@robhost.de>
#
#  Author: Tobias Böhm <tb@robhost.de>
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License as
#  published by the Free Software Foundation; either version 2 of the
#  License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307
#  USA


"""This module provides convenience wrappers for interacting with the
PVE-API through pvesh. As it uses the pvesh tool, it doesn't need any
auth configuration.
"""

from subprocess import Popen, PIPE
import json


class PVESH(object):
    """Object which builds a pvesh command and holds the response when
    it is run.

    Example:
        p = PVESH('get', '/storage/local')  # returns PVESH instance
        p.run()                             # returns PVESH instance
        s = p.asobj()                       # returns new object
        print(s['type'])
    """
    def __init__(self, pveshmethod, pveshpath, **options):
        self.method = pveshmethod.lower()
        self.path = pveshpath
        self.options = options

        self.stdout = None
        self.stderr = None
        self.returncode = None

    @property
    def cmd(self):
        """Return the complete pvesh command line."""
        cmd = ["pvesh", self.method, self.path]
        for option, value in self.options.items():
            cmd.append("-{}".format(option))
            cmd.append(str(value))

        return cmd

    @property
    def hasrun(self):
        """Return if the command has been executed or not."""
        for attr in ('stdout', 'stderr', 'returncode'):
            if getattr(self, attr) is not None:
                return True

        return False

    def asobj(self):
        """Return the stdout as dict if the command already has run and
        the output is valid json. Return None if the command hasn't run.
        Raise Exception if Response is not valid JSON.
        """
        if self.hasrun:
            if self.stdout == '':
                return {}

            try:
                return json.loads(self.stdout)
            except ValueError as exc:
                raise Exception(exc)

        return None

    def run(self):
        """Run the command and return, set the attributes stdout, stderr
        and returncode.
        """
        if not self.hasrun:
            pipe = Popen(self.cmd, stdout=PIPE, stderr=PIPE)
            output = [e.decode() for e in pipe.communicate()]
            self.stdout, self.stderr = output
            self.returncode = pipe.returncode

        return self

    def __bool__(self):
        """Return if the object is considered OK or failed."""
        return self.returncode < 1

    __nonzero__ = __bool__


def get(pveshpath, **options):
    """Wrapper for pvesh get calls."""
    return PVESH('get', pveshpath, **options)

def create(pveshpath, **options):
    """Wrapper for pvesh post calls."""
    return PVESH('create', pveshpath, **options)

def set(pveshpath, **options):
    """Wrapper for pvesh put calls."""
    return PVESH('set', pveshpath, **options)

def delete(pveshpath, **options):
    """Wrapper for pvesh delete calls."""
    return PVESH('delete', pveshpath, **options)

def migratevm(sourcenode, vmtype, vmid, targetnode, **options):
    """Run a VM migration for the given vmid to the given node."""
    path = '/nodes/{}/{}/{}/migrate'.format(sourcenode, vmtype, vmid)
    options['target'] = targetnode
    return create(path, **options)
