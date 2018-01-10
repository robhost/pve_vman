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


import logging

from pve_vman import pvestats


MAXMIGRATIONS = 150
BALDIFFPERC = 5


def planbalance(cluster, iterations=MAXMIGRATIONS, diffperc=BALDIFFPERC):
    """Migrate VMs in order to even the memory usage percentage on the
    nodes. The given cluster is changed.
    """
    _logger = logging.getLogger(__name__)

    def nodediff(diffattr, node1, node2):
        diff = getattr(node1, diffattr) - getattr(node2, diffattr)
        return abs(diff)

    attr = 'memvmnodeused_perc'

    # For a maximum of the given number of iterations, try to move VMs
    # until the memory percentage difference between the nodes is lower
    # than the break condition value. Prefer VMs that already have been
    # moved in order to minimize movement.
    for _ in range(iterations):
        highestnode = cluster.highestnode(attr, lambda c: c.isonline)
        lowestnode = cluster.lowestnode(attr, lambda c: c.isonline)

        if diffperc > nodediff(attr, highestnode, lowestnode):
            break

        vms = highestnode.moved_vms()

        if not vms:
            vms = highestnode.migrateable_vms()

        curvm = vms.pop()
        _logger.debug(str(curvm))

        highestnode.remove(curvm)
        lowestnode.add(curvm)

    return cluster

def planflush(nodes, cluster, onlyha=False, maxmigrations=MAXMIGRATIONS):
    """Migrate all migratable VMs off the given nodes in order to empty
    it, e.g. for maintenance. The given cluster is changed.
    """
    emptynodes = []
    iterations = 0

    for node in nodes:
        if node not in cluster.keys():
            raise Exception("node '{}' doesn't exist".format(node))

        emptynodes.append(cluster[node])

    for emptynode in emptynodes:
        for pvevm in emptynode.migrateable_vms():
            if onlyha and not pvevm.ha:
                continue

            if iterations >= maxmigrations:
                break

            iterations += 1

            emptynode.remove(pvevm)
            lowestnode = cluster.lowestnode(
                'memvmnodeused_perc',
                lambda n: n.isonline and n not in emptynodes)
            lowestnode.add(pvevm)

    return cluster
