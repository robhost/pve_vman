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


"""This module can be used to get a data structure that represents a
PVE cluster based on the stats information the PVE-API provides.
"""

import functools
import re

from pve_vman import pvesh, pvefiles

# python 2 and 3.4 compat
try:
    basestring
except NameError:
    basestring = str


@functools.total_ordering
class PVEStatObject(object):
    """Abstract class that can be used for handling PVE types that
    have stats available, e.g. Nodes or VMs. Inherited classes need to
    set the IDKEY constant to the name of the key that identifies an
    instance.
    """
    IDKEY = "name"

    def __init__(self, **kw):
        """Keyword arguments given will be accessible as attributes."""
        super(PVEStatObject, self).__init__()
        self.attrs = kw
        self.idkey = self.__class__.IDKEY

    def __getattr__(self, attr):
        if attr in self.attrs:
            return self.attrs.get(attr)
        return self.__getattribute__(attr)

    def __repr__(self):
        return str(self.id)

    def __eq__(self, other):
        return self.id == other.id

    def __lt__(self, other):
        return self.id < other.id

    @property
    def id(self):
        """Return the identifier value for this instance."""
        if self.idkey in self.attrs:
            return self.attrs.get(self.idkey)
        raise Exception("idkey '{}' not found in attrs".format(self.idkey))


class PVEStatContainer(object):
    """Abstract class that can be used for handling PVE types that
    have children that inherit from PVEStatObject. It provides
    convenience methods for filtering and fetching min/max childs.
    """
    def __init__(self):
        self.frozen = False
        self.children = []

    def __setattr__(self, key, value):
        if key == "children" and self.frozen:
            raise Exception("object frozen")
        super(PVEStatContainer, self).__setattr__(key, value)

    def __iter__(self):
        return self.children.__iter__()

    def __getitem__(self, key):
        for child in self.children:
            if isinstance(key, basestring):
                if child.id == key:
                    return child
            elif child == key:
                return child
        raise KeyError(key)

    def __delitem__(self, key):
        child = self[key]
        self.children.remove(child)
        return child

    def __contains__(self, key):
        try:
            self[key]
        except KeyError:
            return False
        else:
            return True

    def keys(self):
        """Return a list of identifier for all children."""
        return [c.id for c in self.children]

    def add(self, child):
        """Add child to the container. Needs to inherit from
        PVEStatObject.
        """
        if self.frozen:
            raise Exception('object frozen')
        if not isinstance(child, PVEStatObject):
            raise Exception('child does not inherit from PVEStatObject')
        self.children.append(child)
        return child

    def remove(self, key):
        """Remove a child from the container. Can be identified by the
        id string or the object itself.
        """
        child = self[key]
        self.children.remove(child)
        return child

    def freeze(self):
        """Freeze (and sort) this containers child list and all childs
        that are PVEStatContainers themself recursively.
        """
        if self.frozen:
            return False

        for child in self.children:
            if isinstance(child, PVEStatContainer):
                child.freeze()

        self.children = tuple(sorted(self.children))
        self.frozen = True

        return True

    def csum(self, attr):
        """Return sum over all children of the attribute values for the
        given name.
        """
        return sum([getattr(c, attr) for c in self.children])

    def sortedbyattr(self, attr, reverse=False, filtermethod=None):
        """Get the children list sorted by the attribute with the given
        name. Order can be reversed with reverse=True. If filtermethod
        is a callable, only elements that the callable returns True for
        are sorted and returned.
        """
        if callable(filtermethod):
            arr = self.cfilter(filtermethod)
        else:
            arr = self.children

        return sorted(arr, key=lambda c: getattr(c, attr), reverse=reverse)

    def lowestchild(self, attr, filtermethod=None):
        """Return child that has the lowest value for the given attr.
        filtermethod can be given to match only certain children.
        """
        children = self.sortedbyattr(
            attr,
            filtermethod=filtermethod)

        if children:
            return children[0]

        return None

    def highestchild(self, attr, filtermethod=None):
        """Return child that has the highest value for the given attr.
        filtermethod can be given to match only certain children.
        """
        children = self.sortedbyattr(
            attr,
            reverse=True,
            filtermethod=filtermethod)

        if children:
            return children[0]

        return None

    def cfilter(self, method=lambda c: True):
        """Return list of elements which method returns True for.
        Therefore method needs to be callable.
        """
        return [c for c in self.children if method(c)]


class PVEMigration(object):
    """Represents a VM migration. After initializing, it can be run.
    That calls pvesh to initiate the migration and waits for completion
    of the migration if it is not a HA managed VM.
    """
    def __init__(self, pvevm, target):
        self.pvevm = pvevm
        if isinstance(target, PVEStatNode):
            self.target = str(target.id)
        else:
            self.target = target

        self.pvesh = pvesh.migratevm(
            self.source,
            pvevm.type,
            pvevm.id,
            self.target,
            online=1)

    def __repr__(self):
        fmt = 'Migration: {} from {} to {}'
        return fmt.format(self.pvevm, self.source, self.target)

    @property
    def source(self):
        """Return the name of the node the VM is currently running on.
        """
        return self.pvevm.node

    @property
    def cmd(self):
        """Return the command that will be used to start the migration.
        """
        return self.pvesh.cmd

    def run(self):
        """Run the migration using pvesh."""
        return self.pvesh.run()


class PVEStatCluster(PVEStatContainer):
    """Proxmox Cluster that is the root container containing a list of
    Proxmox nodes as children.
    """
    def clone(self):
        """Return a new PVEStatCluster object that has completely cloned
        children. Changes on the new object will not affect the original
        one.
        """
        cluster = PVEStatCluster()

        for child in self.children:
            node = PVEStatNode(**child.attrs)
            node.children = [PVEStatVM(**v.attrs) for v in child.children]
            cluster.add(node)

        return cluster

    def nodes(self, filtermethod=None):
        """Return a list of all Nodes of the Cluster. If filtermethod is
        given, only Nodes that the filtermethod returns True for are
        considered and returned.
        """
        if filtermethod is None:
            nodelist = self.children
        else:
            nodelist = self.cfilter(filtermethod)

        return [n for n in nodelist]

    def vms(self, filtermethod=None):
        """Return a list of all VMs of the cluster. If filtermethod is
        given, only VMs that the filtermethod returns True for are
        considered and returned.
        """
        return [v for n in self.nodes() for v in n.vms(filtermethod)]

    def lowestnode(self, attr, filtermethod=None):
        """Return the node with the lowest VM utilization indicated
        by the attribute attr for the VMs."""
        return self.lowestchild(attr, filtermethod)

    def highestnode(self, attr, filtermethod=None):
        """Return the node with the highest VM utilization indicated
        by the attribute attr for the VMs."""
        return self.highestchild(attr, filtermethod)

    def lowestvm(self, attr, filtermethod=None):
        """Return the VM with the lowest value of the the attribute
        attr in the cluster. Considered VMs can be filtered by
        a filtermethod.
        """
        vms = [c.lowestvm(attr, filtermethod) for c in self.children]
        sorted_vms = sorted([vm for vm in vms if vm is not None])

        return sorted_vms[0] if sorted_vms else None

    def highestvm(self, attr, filtermethod=None):
        """Return the VM with the highest value of the the attribute
        attr in the cluster. Considered VMs can be filtered by
        a filtermethod.
        """
        vms = [c.highestvm(attr, filtermethod) for c in self.children]
        sorted_vms = sorted([vm for vm in vms if vm is not None])

        return sorted_vms[-1] if sorted_vms else None

    def migrations(self):
        """Return all migrations that are necessary to reach the target
        state of the cluster.
        """
        return [m for n in self.nodes() for m in n.migrations()]


class PVEStatNode(PVEStatObject, PVEStatContainer):
    """Proxmox Node instance. Container for VMs."""
    IDKEY = "node"

    def __repr__(self):
        return "Node {}".format(self.node)

    @property
    def memnodeused_gb(self):
        """Return used memory for the node in GB."""
        return float(self.mem) / 1024**3

    @property
    def memnodetotal_gb(self):
        """Return total memory for the node in GB."""
        return float(self.maxmem) / 1024**3

    @property
    def memvmprov(self):
        """Return sum of provisoned memory for all VMs."""
        return self.csum('maxmem')

    @property
    def memvmused(self):
        """Return sum of used memory for all VMs."""
        return self.csum('mem')

    @property
    def memvmused_gb(self):
        """Return memory used by VMs on the node in GB."""
        return float(self.memvmused) / 1024**3

    @property
    def memvmprovisioned_gb(self):
        """Return memory provisined for VMs on the node in GB."""
        return float(self.memvmprov) / 1024**3

    def vms(self, filtermethod=None):
        """Return a list of all VMs of the Node. If filtermethod is
        given, only VMs that the filtermethod returns True for are
        considered and returned.
        """
        if filtermethod is None:
            vmlist = self.children
        else:
            vmlist = self.cfilter(filtermethod)

        return [v for v in vmlist]

    def migrateable_vms(self):
        """Return list of VMs that are migrateable."""
        return self.vms(lambda c: c.migrateable)

    def lowestvm(self, attr, filtermethod=None):
        """Return the VM with the lowest value of the the attribute
        attr on the node. Considered VMs can be filtered by
        a filtermethod.
        """
        return self.lowestchild(attr, filtermethod)

    def highestvm(self, attr, filtermethod=None):
        """Return the VM with the highest value of the the attribute
        attr on the node. Considered VMs can be filtered by
        a filtermethod.
        """
        return self.highestchild(attr, filtermethod)

    def migrations(self):
        """Return all migrations that are necessary to reach the target
        state of the cluster.
        """
        vms = self.migrateable_vms()

        return [vm.migration(self) for vm in vms if vm.needsmove(self)]


class PVEStatVM(PVEStatObject):
    """Proxmox VM instance."""
    IDKEY = "vmid"

    def __repr__(self):
        return 'VM {}'.format(self.id)

    @property
    def memused_gb(self):
        """Return memory used by the VM in GB."""
        return float(self.mem) / 1024**3

    @property
    def memprovisioned_gb(self):
        """Return memory provisioned for the VM in GB."""
        return float(self.maxmem) / 1024**3

    def needsmove(self, target):
        """Return if the VM is needs a migration to run on the target
        node.
        """
        return target.node != self.node

    def migration(self, target):
        """Return PVEMigration instance for the VM."""
        return PVEMigration(self, target)


def getresources():
    """Return cluster resources as a dict."""
    return pvesh.get('/cluster/resources').run().asobj()

def getharesources():
    """Return cluster ha resources as a dict."""
    return pvesh.get('/cluster/ha/resources').run().asobj()

def buildcluster(resources=None, haresources=None):
    """Return a PVEStatCluster object built using the given
    resources dict and haresources dict. If none given, get these using
    the getresource() and getharesources() methods.
    """
    vmconf = pvefiles.getvmconf()
    storageconf = pvefiles.getstorageconf()
    diskpattern = re.compile(r'^(?:rootfs|(?:scsi|sata|virtio|ide|mount)\d+)$')

    def ismigrateable(vmid):
        """Return if the VM with the given ID is migrateable. A VM is
        considered not migrateable, if a storage backend is used that is
        not rbd, nfs or iscsi.
        """
        for name, opts in vmconf[str(vmid)].items():
            if diskpattern.match(name) and ':' in opts:
                storage = opts.split(':')[0]
                if storageconf[storage]['type'] not in ['rbd', 'nfs', 'iscsi']:
                    return False
        return True

    if resources is None:
        resources = getresources()

    if haresources is None:
        haresources = getharesources()

    hadict = {int(hr['sid'].split(':')[1]): hr for hr in haresources}

    cluster = PVEStatCluster()

    for resource in resources:
        if resource['type'] == 'node':
            cluster.add(PVEStatNode(**resource))

    for resource in resources:
        if resource['type'] not in ('node', 'storage'):
            node = cluster[resource['node']]
            haresource = hadict.get(resource['vmid'], {})
            resource['ha'] = len(haresource) != 0
            resource['haenabled'] = haresource.get('state', '') == 'enabled'
            resource['hagroup'] = haresource.get('group', None)
            resource['migrateable'] = ismigrateable(resource['vmid'])
            node.add(PVEStatVM(**resource))

    return cluster
