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


"""This module provides functions for calculating VM distribution across
the nodes of the cluster by different criteries like freeing up a node
or balancing VMs across all nodes.
"""


from pve_vman import pvestats


def planbalance(cluster=None):
    """Migrate VMs in order to even the memory usage on the nodes. The
    given cluster is not changed. Instead it is cloned and the new
    instance is changed and returned.
    """
    def nodememdiff(cluster):
        """Return the difference of memeory between the node with the
        highest memory usage and the one with the lowest.
        """
        high = cluster.highestnode(attr)
        low = cluster.lowestnode(attr)
        return getattr(high, attr) - getattr(low, attr)

    if cluster is None:
        cluster = pvestats.buildcluster()

    cluster.freeze()

    attr = 'memvmused'
    newcluster = cluster.clone()
    highestvm = cluster.highestvm('mem', lambda c: c.migrateable)

    if highestvm is None:
        return newcluster

    iterations = 100
    i = 0

    # For a maximum of the given number of iterations, try to move VMs
    # until the memory difference between the nodes is lower than the
    # memory usage of the VM with the highest memory usage.
    while i < iterations and nodememdiff(newcluster) > highestvm.mem:
        highestnode = newcluster.highestnode(attr)
        lowestnode = newcluster.lowestnode(attr)
        curvm = highestnode.migrateable_vms().pop()
        highestnode.remove(curvm)
        lowestnode.add(curvm)
        i += 1

    return newcluster

def planflush(node, onlyha=False, cluster=None):
    """Migrate all migratable VMs off the given node in order to empty
    it, e.g. for maintenance. The given cluster is not changed. Instead
    it is cloned and the new instance is changed and returned.
    """
    if cluster is None:
        cluster = pvestats.buildcluster()

    cluster.freeze()

    if node not in cluster.keys():
        raise Exception("node '{}' doesn't exist".format(node))

    newcluster = cluster.clone()
    emptynode = newcluster[node]
    newcluster.remove(node)

    for pvevm in emptynode.migrateable_vms():
        if onlyha and not pvevm.ha:
            continue
        emptynode.remove(pvevm)
        lowestnode = newcluster.lowestnode('memvmused')
        lowestnode.add(pvevm)

    return newcluster
