# -*- coding: utf-8 -*-

# dev stub

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

    if os.path.exists(fullpath):
        return _readfile(fullpath)
    else:
        return []

def storageconf():
    """Return dictionary of the PVE cluster storage configuration."""
    filecontent = readpvefile('storage.cfg')
    conf = {}
    current = {}

    for line in filecontent:
        line_a = line.split()

        if not line_a:
            continue

        key = line_a[0]
        value = (' ').join(line_a[1:])

        if key.endswith(':'):
            current = conf[value] = {
                'name': value,
                'type': key[:-1],
                'shared': '1'}
        else:
            current[key] = value

    return conf

def vmconf():
    """Return dictionary of the PVE cluster VM configurations."""
    pattern = os.path.join(BASEPATH, 'nodes', '*', '*', '*.conf')
    conf = {}

    for filepath in glob.iglob(pattern):
        pathparts = filepath.split(os.path.sep)

        if pathparts[-2] not in ['qemu-server', 'lxc']:
            continue

        vmtype = pathparts[-2]
        vmid = pathparts[-1][:-5]
        vmnode = pathparts[-3]

        current = conf[vmid] = {
            'vmid': vmid,
            'type': vmtype,
            'node': vmnode}

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

    return conf

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
            if value and not (value == 'U' and conv is not str):
                stat[key] = conv(value)
            else:
                stat[key] = conv()

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

        key = line_a[0]
        value = (' ').join(line_a[1:])

        if key.endswith(':'):
            current = conf[value] = {'name': value, 'type': key[:-1]}
        elif isinstance(current, dict):
            current[key] = value

    return conf
