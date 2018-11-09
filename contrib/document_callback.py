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

import prettytable
import yaml

from callback_plugins import baseline


def default(data):
    if data['type'] == 'bool':
        if data.get('default', False):
            return '(yes)/no'
        return 'yes/(no)'
    return data['default']


def bool_to_string(v):
    if v is True:
        return 'yes'
    elif v is False:
        return 'no'
    return v


def config(data):
    out = []
    for section in data.get('ini', []):
        out.append('[%s]' % section['section'])
        out.append(
            '%s = %s' % (section['key'], bool_to_string(data['default']))
        )
    out.append('')
    for section in data.get('env'):
        out.append('env:%s' % section['name'])

    return '<br>'.join(out)


def normalize(v):
    return v.replace('_', '\_').replace('``', '`')


def main():
    doc = yaml.safe_load(baseline.DOCUMENTATION)
    x = prettytable.PrettyTable(
        ['Parameter', 'Choices/Defaults', 'Configuration', 'Comments']
    )
    for k in x.align:
        x.align[k] = 'l'

    options = doc.get('options', {})
    for param, data in sorted(options.items(), key=lambda t: t[0]):
        x.add_row([normalize(i) for i in (
            param,
            default(data),
            config(data),
            data['description']
        )])

    print('\n'.join(x.get_string(junction_char='|').splitlines()[1:-1]))


if __name__ == '__main__':
    main()
