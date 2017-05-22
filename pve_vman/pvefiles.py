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

from collections import defaultdict


BASEPATH = '/etc/pve'
"""Path to the PVE cluster configuration directory."""


def _readfile(filepath):
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
    return _readfile(fullpath)

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

        filecontent = _readfile(filepath)

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

def stats():
    keys_by_prefix = {
        'pve2-storage': (
            ('storage', str),
            ('timestamp', int),
            ('total', int),
            ('used', int)),
        'pve2-node': (
            ('node', str),
            ('uptime', int),
            ('level', str),
            ('timestamp', int),
            ('load', float),
            ('maxcpu', int),
            ('cpu', float),
            ('iowait', float),
            ('memtotal', int),
            ('memused', int),
            ('swaptotal', int),
            ('swapused', int),
            ('roottotal', int),
            ('rootused', int),
            ('netin', int),
            ('netout', int)),
        'pve2.3-vm': (
            ('vmid', str),
            ('uptime', int),
            ('name', str),
            ('status', str),
            ('template', str),
            ('timestamp', int),
            ('maxcpu', int),
            ('cpu', float),
            ('maxmem', int),
            ('mem', int),
            ('maxdisk', int),
            ('disk', int),
            ('netin', int),
            ('netout', int),
            ('diskread', int),
            ('diskwrite', int))
        }

    def parseline(line):
        line_a = line.split(':')
        identifier = line_a[0].split('/')
        prefix = identifier[0]
        line_a[0] = identifier[1]
        stattype = prefix.split('-')[-1]
        stat = {'type': stattype, 'prefix': prefix}
        keys = keys_by_prefix.get(prefix, [])

        for (key, conv), value in zip(keys, line_a):
            stat[key] = conv(value) if value else conv()

        return stat

    filecontent = readpvefile('.rrd')
    stats_d = defaultdict(list)

    for line in filecontent:
        stat = parseline(line.strip())
        stats_d[stat['type']].append(stat)

    return dict(stats_d)

def haconf():
    filecontent = readpvefile('ha/resources.cfg')
    conf = {}

    for line in filecontent:
        line_a = line.split()

        if not line_a:
            continue

        key, value = line_a

        if key.endswith(':'):
            current = conf[value] = {'name': value, 'type': key[:-1]}
        elif isinstance(current, dict):
            current[key] = value

    return conf
