#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) 2018, Matt Martz <matt@sivel.net>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import argparse
import importlib

import prettytable
import yaml

from callback_plugins import baseline


def default(data):
    if data.get('type') == 'bool':
        if data.get('default', False):
            return '(yes)/no'
        return 'yes/(no)'
    return data.get('default')


def bool_to_string(v):
    if v is True:
        return 'yes'
    elif v is False:
        return 'no'
    return v


def config(data):
    out = []
    ini = data.get('ini', [])
    #if ini:
    #    out.append('ini entries:')
    for section in ini:
        out.append('[%s]' % section['section'])
        out.append(
            '%s = %s' % (section['key'], bool_to_string(data.get('default')))
        )
    out.append('')
    for section in data.get('env'):
        out.append('env:%s' % section['name'])

    return '<br>'.join(out)


def normalize(v):
    try:
        return v.replace('_', '\_').replace('``', '`')
    except AttributeError:
        if v is None:
            return ''
        return v


def param(name, data):
    if data.get('required'):
        return '%s<br>(required)' % name
    return name


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('module', nargs='?', default='callback_plugins.baseline')
    args = parser.parse_args()
    try:
        module = importlib.import_module(args.module)
    except ImportError as e:
        raise SystemExit('Could not import %s: %s' % (args.module, e))
    doc = yaml.safe_load(module.DOCUMENTATION)
    x = prettytable.PrettyTable(
        ['Parameter', 'Choices/Defaults', 'Configuration', 'Comments']
    )
    for k in x.align:
        x.align[k] = 'l'

    options = doc.get('options', {})
    for name, data in sorted(options.items(), key=lambda t: t[0]):
        x.add_row([normalize(i) for i in (
            param(name, data),
            default(data),
            config(data),
            data['description']
        )])

    print('\n'.join(x.get_string(junction_char='|').splitlines()[1:-1]))


if __name__ == '__main__':
    main()
