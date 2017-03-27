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


"""This module provides functions for interacting with the QEMU monitor
via its unix socket."""

import os
import sys
import socket
import json


class PVEQEMUMonitor(object):
    """Object for handling communication with the QEMU Monitor."""

    socketpath_fmt = '/var/run/qemu-server/{}.qmp'

    def __init__(self, vmid, socketpath=None):
        if socketpath is None:
            socketpath = PVEQEMUMonitor.socketpath_fmt.format(vmid)

        self.vmid = vmid
        self.sock = None
        self.socketpath = socketpath

    def connect(self):
        """Connect to the QemuMonitor and initiate the session. This
        will open a socket and set the sock attribute."""
        if not os.path.exists(self.socketpath):
            raise Exception('no monitor socket found. VM not running')
        try:
            self.sock = socket.socket(
                socket.AF_UNIX,
                socket.SOCK_STREAM
                )
            self.sock.connect(self.socketpath)
            self.sock.settimeout(0.1)
            self.receive()
            self.send(execute='qmp_capabilities')
            self.receive()
        except:
            self.disconnect()
            raise

    def disconnect(self):
        """Close the socket and unset the sock attribute."""
        if self.sock is not None:
            self.sock.close()
            self.sock = None

    def send(self, **kwargs):
        """The given args dict will be convertted to JSON and send to
        the monitor. Might raise JSON errors if the dict can't be
        converted.
        """
        assert self.sock is not None
        cmd = json.dumps(kwargs)
        self.sock.send(cmd.encode())

    def receive(self):
        """Return JSON decoded object of the string read from the
        monitor socket. Raises exception if the answer contains error
        messages.
        """
        assert self.sock is not None
        ret = json.loads(self.sock.recv(4096).decode())

        if 'return' in ret:
            return ret['return']
        elif 'error' in ret:
            raise Exception(ret['error'])

    def human_cmd(self, cmd):
        """Return JSON decoded object of the answer following the given
        human-monitor-command.
        """
        self.send(
            execute='human-monitor-command',
            arguments={'command-line': cmd}
            )

        return self.receive()


def query_blockstats(vmid):
    """Return blockstats dictionary read from QEMU monitor."""
    pqm = PVEQEMUMonitor(vmid)
    pqm.connect()
    pqm.send(execute='query-blockstats')

    return pqm.receive()


if __name__ == '__main__':
    if len(sys.argv) >= 2:
        print(query_blockstats(sys.argv[1]))
    else:
        print('no vm id given')
