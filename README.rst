PVE-vman
========

RobHost GmbH [support@robhost.de], 2017

License: GPLv2+

PLEASE NOTE THAT THIS SOFTWARE COMES WITH ABSOLUTELY NO WARRANTY!


What is it good for?
--------------------

Handling a lot of VMs on a PVE cluster can be tedious. VMs might be
unevenly distributed across nodes or imagine you want to due maintanace
work on a node and migrate the VMs off to other nodes evenly and after
finishing the maintenance distribute VMs evenly across all nodeds again.

That's where pve-vman comes in. It provides commands to migrate all
migratebale VMs off a given node or balance VMs across all nodes based
on the memory used by the VMs.


Requirements
------------

- Proxmox VE cluster 4
- Access to pvesh tool


Installation
------------

::

    python setup.py install


Usage
-----

Print current cluster status::

    vman status

Balance VMs across all nodes::

    vman balance

Migrate all migrateable VMs off a node, but only calculate necessary
steps, don't execute::

    vman flush --noexec pvenode03

Run a flush, but only consider VMs that have HA enabled::

    vman flush --onlyha pvenode02
