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
import csv
import datetime
import json

from io import StringIO

try:
    from itertools import izip as zip
except ImportError:
    pass


def iso2date(v):
    return datetime.datetime.strptime(v, '%Y-%m-%dT%H:%M:%S.%f')


def iso_sort(tup):
    dummy, data = tup
    return iso2date(data['duration']['start'])


def delta_s(start, end):
    return round((iso2date(end) - iso2date(start)).total_seconds(), 2)


def starts_ends_lag(task, host):
    starts = [t['task']['duration']['start'] for t in task]
    ends = [h[1]['duration']['start'] for h in host]
    return zip(starts, ends)


def hosts_lag(task):
    hosts_lists = [sorted(t['hosts'].items(), key=iso_sort) for t in task]

    return zip(*hosts_lists)


def starts_ends_duration(task, host):
    starts = [h[1]['duration']['start'] for h in host]
    ends = [h[1]['duration']['end'] for h in host]
    return zip(starts, ends)


def hosts_duration(task):
    hosts = [t[0] for t in sorted(task[0]['hosts'].items(), key=iso_sort)]
    hosts_lists = []
    for t in task:
        hosts_lists.append([(host, t['hosts'][host]) for host in hosts])
    return zip(*hosts_lists)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('files', nargs='+')
    parser.add_argument('-d', '--duration', action='store_true',
                        help='Calculate host duration, instead of queued time')
    return parser.parse_args()


def main():
    args = parse_args()
    items = []
    for i, filename in enumerate(args.files):
        with open(filename) as f:
            items.append(json.load(f))

    f = StringIO()
    w = csv.writer(f)

    w.writerow(['Play', 'Task', 'Host'] + args.files)

    for i, play in enumerate(items[0]):

        tasks = zip(*(item[i]['tasks'] for item in items))

        for task in tasks:
            name = task[0]['task']['name']

            if args.duration:
                hosts = hosts_duration(task)
            else:
                hosts = hosts_lag(task)

            for i, host in enumerate(hosts):
                if args.duration:
                    starts_ends = starts_ends_duration(task, host)
                    host_name = host[0][0]
                else:
                    starts_ends = starts_ends_lag(task, host)
                    host_name = 'host%s' % (i + 1)
                deltas = [delta_s(*sd) for sd in starts_ends]

                w.writerow([play['play']['name'], name, host_name] + deltas)

    try:
        print(f.getvalue())
    except IOError:
        pass


if __name__ == '__main__':
    main()
