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


"""VMIOStats"""


import glob
import os

from pve_vman import pveqemumonitor


class VMIOStats(object):

    keys = ('rd_bytes', 'rd_operations', 'wr_bytes', 'wr_operations')

    def __init__(self, interval, pathglob = '/run/qemu-server/*.qmp'):
        self.interval = interval
        self.pathglob = pathglob
        self.vmstats = {}

    def qmpaths(self):
        return sorted(glob.iglob(self.pathglob))

    def get_vmstats(self, vmid):
        if vmid not in self.vmstats:
            self.vmstats[vmid] = self._new_statdict()
        return self.vmstats[vmid]

    def fetch(self):
        vmdiffs = {}
        vmsums = self._new_statdict()

        for qmpath in self.qmpaths():
            vmid = os.path.basename(qmpath).split(".")[0]

            try:
                blockstats = pveqemumonitor.query_blockstats(vmid)
            except:
                continue

            stats = self.get_vmstats(vmid)
            diffs = {}

            for key in stats.keys():
                statsum = sum([d['stats'][key] for d in blockstats])
                diffs[key] = (statsum - stats[key])/self.interval
                stats[key] = statsum
                vmsums[key] += diffs[key]

            vmdiffs[vmid] = diffs

        return (vmdiffs, vmsums)

    def _new_statdict(self):
        return  dict(zip(VMIOStats.keys, (0,0,0,0)))

