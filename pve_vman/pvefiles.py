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


"""This module provides the ability to read PVE cluster config files
into python data structures.
"""


import os
import glob


BASEPATH = '/etc/pve'
"""Path to the PVE cluster configuration directory."""


def readfile(filepath):
    """Return content of the file found at the given file path. Raises
    FileNotFoundError if the file doesn't exist and IOError if the file
    is not readable.
    """
    with open(filepath) as fileh:
        return fileh.readlines()

def readpvefile(pvefilepath):
    """Return raw content of the file given by the relative path to the
    PVE config directory.
    """
    fullpath = os.path.join(BASEPATH, pvefilepath)
    return readfile(fullpath)

def getstorageconf():
    """Return dictionary of the PVE cluster storage configuration."""
    filecontent = readpvefile('storage.cfg')
    storageconf = {}
    current = None

    for line in filecontent:
        line_a = line.split()

        if not line_a:
            continue

        key, value = line_a

        if key.endswith(':'):
            current = storageconf[value] = dict(
                handle=value,
                type=key[:-1],
                shared='1'
            )
        elif isinstance(current, dict):
            current[key] = value

    return storageconf

def getvmconf():
    """Return dictionary of the PVE cluster VM configurations."""
    pattern = os.path.join(BASEPATH, 'nodes', '*', '*', '*.conf')
    configfiles = glob.glob(pattern)
    vmconf = {}
    current = None

    for filepath in configfiles:
        pathparts = filepath.split(os.path.sep)
        vmid = pathparts[-1][:-5]
        vmtype = pathparts[-2]
        vmnode = pathparts[-3]

        current = vmconf[vmid] = dict(
            vmid=vmid,
            type=vmtype,
            node=vmnode
        )

        filecontent = readfile(filepath)

        for line in filecontent:
            line_a = line.split()

            if not line_a:
                continue
            elif line.startswith('[PENDING]'):
                current = current['pending'] = {}
                continue
            # Handle if there is only one element on the line, which
            # indicates a seperate config section start (just as the
            # PENDING section, for example start of a snapshot conf
            # ("[<snapshotname>]")
            elif len(line_a) < 2:
                continue

            # first element is the key suffixed with a colon which we strip
            key = line_a[0][:-1]
            value = line_a[1]

            current[key] = value

    return vmconf
