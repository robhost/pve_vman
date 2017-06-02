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


"""CLI command handler"""


from __future__ import print_function

import argparse
import sys
import time
import signal
import logging

from pve_vman import pvestats, pvecluster, pvevmiostats

logging.basicConfig(format='%(message)s')


class _VerbosityAction(argparse.Action):
    def __init__(self, option_strings, dest, **_):
        super(_VerbosityAction, self).__init__(
            option_strings=option_strings,
            dest=dest,
            nargs=0,
            default=None,
            required=False,
            help=None)

    def __call__(self, parser, namespace, values, option_string=None):
        logger = logging.getLogger()
        current_level = logger.getEffectiveLevel()
        if current_level > logging.DEBUG:
            logger.setLevel(current_level - 10)

def __int_fmt(num, base=1000):
    for unit in ['', 'K', 'M', 'G', 'T', 'P']:
        if abs(num) < 10000:
            return "%d%s" % (num, unit)
        num /= base
    return num

def print_state(cluster):
    """Format and print the given cluster object."""
    lines = []
    migrateable = lambda c: c.migrateable
    havms = lambda c: c.ha

    for node in cluster:
        lines.append((
            'Node {}'.format(node.node),
            __int_fmt(node.memtotal, base=1024),
            node.memused_perc,
            node.memvmnodeused_perc,
            node.memvmnodeprov_perc,
            len(node.children),
            len(node.vms(migrateable)),
            len(node.vms(havms))))

    lines.append((
        'Cluster',
        __int_fmt(cluster.memtotal, base=1024),
        cluster.memused_perc,
        cluster.memvmclusterused_perc,
        cluster.memvmclusterprov_perc,
        len(cluster.vms()),
        len(cluster.vms(migrateable)),
        len(cluster.vms(havms))))

    fmt_first = '{{:{:d}s}}'.format(max([len(l[0]) for l in lines]))
    fmt_h1 = fmt_first
    fmt_h1 += ' | {:^12s} | {:^11s} | {:^18s}'
    fmt_h2 = fmt_first
    fmt_h2 += ' | {:^5s} | {:^4s} | {:^4s} | {:^4s} | {:^4s} | {:^4s} | {:^4s}'
    fmt_d = fmt_first
    fmt_d += ' | {:>5s} | {:3d}% | {:3d}% | {:3d}%'
    fmt_d += ' | {:4d} | {:4d} | {:4d}'

    print(fmt_h1.format('', 'Node Mem', 'VM Mem Sums', 'VM Counts'))
    print(fmt_h2.format('', 'Total', 'Used', 'Used', 'Prov', 'Tot.', 'Migr',
                        'HA'))
    for line in lines:
        print(fmt_d.format(*line))

def exec_migrate(cluster, newcluster, args):
    """Run the necessary VM migrations in order to achive the state
    defined by the newcluster object.
    """
    _logger = logging.getLogger(__name__)
    migrations = newcluster.migrations()

    print('===== Current state =====')
    print_state(cluster)
    print('======= New state =======')
    print_state(newcluster)

    _logger.info('Running %d migrations', len(migrations))

    for migration in migrations:
        _logger.info("Running '%s'", migration)
        _logger.debug(' '.join(migration.cmd))

        if args.noexec:
            _logger.info('dry run -- skipping migration')
            continue

        out = migration.run()
        _logger.info(out.stderr)
        _logger.debug(out.stdout)
        if out.returncode != 0:
            raise Exception('migration returncode != 0')

def print_vmiostat(interval=1, count=0, limit=0, totals=False, ssum=False):
    """Print the throughput per VM. Default is to print a line per VM
    and an additional line for the totals. I fno count is given, it runs
    indefinitely until SIGINT is received else it runs count times and then
    terminates.
    """
    def signal_handler(*_):
        print()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    if not totals and count > 0:
        count += 1

    fmt = '{:10} {:>15} {:>15} {:>15} {:>15}'
    keys = pvevmiostats.VMIOStats.keys
    int_fmt = lambda l: [__int_fmt(l[k]) for k in keys]
    vmstats = pvevmiostats.VMIOStats(interval)

    i = 0
    while count == 0 or i < count:
        i += 1
        (vmdiffs, vmsums) = vmstats.fetch()

        if i > 1 or totals:
            print(fmt.format('VM-ID', *keys))

            if not ssum:
                for vmid, diffs in sorted(vmdiffs.items()):
                    if limit == 0 or limit == int(vmid):
                        print(fmt.format(vmid, *int_fmt(diffs)))

            print(fmt.format('total', *int_fmt(vmsums)))

        time.sleep(interval)
        print("")


def command_balance(parser, input_args):
    """Migrate VMs in order to achieve a memeory balanced state."""
    parser.add_argument(
        '-v', '--verbose',
        action=_VerbosityAction,
        help='increase verbosity level, can be used multiple times')
    parser.add_argument(
        '-n', '--noexec',
        action='store_true',
        help='only show, don\'t migrate')
    parser.add_argument(
        '-c', '--count',
        type=int,
        help='number of migrations to run')

    args = parser.parse_args(input_args)

    cluster = pvestats.buildcluster()
    cluster.freeze()

    options = {}
    if 'count' in args and args.count:
        options['iterations'] = args.count

    newcluster = pvecluster.planbalance(cluster.clone(), **options)

    exec_migrate(cluster, newcluster, args)

def command_flush(parser, input_args):
    """Migrate all migrateable VMs off the given Node."""
    parser.add_argument(
        '-v', '--verbose',
        action=_VerbosityAction,
        help='increase verbosity level, can be used multiple times')
    parser.add_argument(
        '-n', '--noexec',
        action='store_true',
        help='only show, don\'t migrate')
    parser.add_argument(
        '-c', '--count',
        type=int,
        help='number of migrations to run')
    parser.add_argument(
        '-o', '--onlyha',
        action='store_true',
        help='only migrate HA managed VMs')
    parser.add_argument(
        'node',
        help='name of the node to migrate all VMs off')

    args = parser.parse_args(input_args)

    cluster = pvestats.buildcluster()
    cluster.freeze()

    options = {'onlyha': args.onlyha}
    if 'count' in args and args.count:
        options['maxmigrations'] = args.count

    newcluster = pvecluster.planflush(args.node, cluster.clone(), **options)

    exec_migrate(cluster, newcluster, args)

def command_status(parser, input_args):
    """Print current cluster status."""
    parser.parse_args(input_args)

    cluster = pvestats.buildcluster()
    cluster.freeze()
    print_state(cluster)

def command_vmiostat(parser, input_args):
    """Print IO stats per VM and sum."""
    def over_zero(value):
        ivalue = int(value)
        if ivalue < 1:
            raise argparse.ArgumentTypeError("%s must be 1 or higher" % value)
        return ivalue

    parser.add_argument(
        '-i', '--interval',
        type=over_zero,
        default=1,
        help='interval of output (>0)')
    parser.add_argument(
        '-c', '--count',
        type=int,
        default=0,
        help='number of iterations (0 = infinite)')
    parser.add_argument(
        '-l', '--limit',
        type=int,
        default=0,
        help='only show stats of VM with this id (0 = all)')
    parser.add_argument(
        '-t', '--totals',
        action='store_true',
        help='show inital totals')
    parser.add_argument(
        '-s', '--sum',
        dest='ssum',
        action='store_true',
        help='show summary only')

    args = parser.parse_args(input_args)

    print_vmiostat(**dict(args._get_kwargs()))


def cli():
    """Parse arguments and call matching handler."""
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(
        dest='command',
        title='commands')

    subparsers.add_parser(
        'balance',
        add_help=False,
        help='migrate VMs to reach an even distribution across nodes')
    subparsers.add_parser(
        'flush',
        add_help=False,
        help='migrate VMs from the given node')
    subparsers.add_parser(
        'status',
        add_help=False,
        help='show the current cluster status')
    subparsers.add_parser(
        'vmiostat',
        add_help=False,
        help='print IO stats for VMs')

    args, exceding_args = parser.parse_known_args()

    if args.command is None:
        parser.print_help()
        sys.exit()

    progname = '{} {}'.format(parser.prog, args.command)
    cmd_parser = argparse.ArgumentParser(prog=progname)

    funcname = 'command_{}'.format(args.command)
    func = globals()[funcname]

    func(cmd_parser, exceding_args)


if __name__ == '__main__':
    cli()
