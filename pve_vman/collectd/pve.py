#!/usr/bin/env python
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

import socket

import collectd

import collectd_common
from pve_vman import pvestats, pveqemumonitor


plugin_metrics = dict(
    PVE_VM_Net_Bytes = dict(
        if_octets = ('netin', 'netout')
    ),
    PVE_VM_Disk_Bytes = dict(
        disk_octets = ('diskread', 'diskwrite')
    ),
    PVE_VM_Disk_IOPS = dict(
        disk_ops = ('diskrops', 'diskwops')
    )
)


def readstats():
    cluster = pvestats.buildcluster()
    hostname = socket.gethostname()
    node = cluster[hostname]

    for vm in node.vms(lambda c: c.status == 'running'):
        if vm.type == 'qemu':
            blockstat = pveqemumonitor.query_blockstats(vm.vmid)
            vm.diskrops = sum([d['stats']['rd_operations'] for d in blockstat])
            vm.diskwops = sum([d['stats']['wr_operations'] for d in blockstat])
        for plugin, metrics in plugin_metrics.items():
            for metric, attrs in metrics.items():
                try:
                    values = [getattr(vm, attr) for attr in attrs]
                except AttributeError:
                    continue
                instance = "VM_%s" % vm.vmid
                collectd_common.dispatch(plugin, instance, metric, None,
                                         values)


collectd.register_read(readstats)
