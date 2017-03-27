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

from setuptools import setup, find_packages
from textwrap import dedent

setup(
    name="pve_vman",
    version="0.1",
    author="Tobias Böhm",
    author_email="tb@robhost.de",
    maintainer="Tobias Böhm",
    maintainer_email="tb@robhost.de",
    url="https://github.com/robhost/pve_vman",
    description="PVE cluster tool for managing distribution of VMs",
    license = 'GPLv2+ <http://www.gnu.org/licenses/gpl-2.0.en.html>',
    keywords="pve proxmox cluster",
    classifiers=dedent("""
        License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)
        Programming Language :: Python :: 3
        Programming Language :: Python :: 3.4
        Topic :: System :: Systems Administration
        Topic :: Utilities
        """).strip().splitlines(),
    python_requires='>=3.4',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'vman = pve_vman.cli:cli'
            ]
        },
    include_package_data = True
)
