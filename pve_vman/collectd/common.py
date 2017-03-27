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

import traceback

import collectd


def dispatch(plugin, plugin_instance, type, type_instance, values,
             interval=60.0):
    print(locals())
    val = collectd.Values(type = type)
    val.plugin = plugin

    if plugin_instance is not None:
        val.plugin_instance = plugin_instance

    if type_instance is not None:
        val.type_instance = type_instance

    if any(isinstance(values, e) for e in [list , tuple]):
        val.values = values
    else:
        val.values = [values]

    val.interval = interval

    try:
        val.dispatch()
    except Exception as exc:
        collectd.error("%s: failed to dispatch values :: %s :: %s"
                % (plugin, exc, traceback.format_exc()))

