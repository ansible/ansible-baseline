# (c) 2016 Matt Martz <matt@sivel.net>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    callback: baseline
    short_description: Ansible baseline recap
    description:
        - This callback will output info usable for baselining plays and tasks
    type: aggregate
    options:
      show_host_timings:
        name: Show host timings
        description: This adds host timings per task
        default: True
        env:
          - name: BASELINE_SHOW_HOST_TIMINGS
        ini:
          - key: show_host_timings
            section: baseline
        type: bool
'''

import datetime

from functools import partial

from ansible.inventory.host import Host

from ansible.executor.process.worker import WorkerProcess

from ansible.plugins.callback import CallbackBase


def current_time():
    return datetime.datetime.utcnow()


class CallbackModule(CallbackBase):
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'aggregate'
    CALLBACK_NAME = 'baseline'

    def __init__(self, display=None):
        super(CallbackModule, self).__init__(display)
        self.results = []
        self._host_start = {}
        self._show_host_timings = True

        WorkerProcess.__init__ = self._infect_worker(WorkerProcess.__init__)

    def _infect_worker(self, func):
        """Intended to wrap ``WorkerProcess.__init__`` and log the start time for a host

        Please don't do this elsewhere, it's bad enough I'm doing it here.
        """
        def inner(*args):
            host = args[3]
            self._host_start[host.name] = current_time()
            func(*args)
        return inner

    def _new_play(self, play):
        return {
            'play': {
                'name': play.get_name(),
                'id': str(play._uuid),
                'duration': {
                    'start': current_time()
                }
            },
            'tasks': []
        }

    def _new_task(self, task):
        self._host_start = {}
        return {
            'task': {
                'name': task.get_name(),
                'id': str(task._uuid),
                'duration': {
                    'start': current_time()
                }
            },
            'hosts': {}
        }

    def set_options(self, options):
        super(CallbackModule, self).set_options(options)

        try:
            self._show_host_timings = self.get_option('show_host_timings')
        except TypeError:
            # Ansible 2.4
            self._show_host_timings = self._plugin_options['show_host_timings']

    def v2_playbook_on_play_start(self, play):
        self.results.append(self._new_play(play))

    def v2_playbook_on_task_start(self, task, is_conditional):
        self.results[-1]['tasks'].append(self._new_task(task))

    def v2_playbook_on_handler_task_start(self, task):
        self.results[-1]['tasks'].append(self._new_task(task))

    def _convert_host_to_name(self, key):
        if isinstance(key, (Host,)):
            return key.get_name()
        return key

    def _print_stat(self, start, end, char='*'):
        columns = self._display.columns
        fill = columns - len(start) - len(end) - 2
        self._display.display('%s %s %s' % (start, char * fill, end))

    def v2_playbook_on_stats(self, stats):
        """Display info about playbook statistics"""

        for play in self.results:
            try:
                play_duration = play['play']['duration']['end'] - play['play']['duration']['start']
            except KeyError:
                # This may fail if the playbook was limited by tags
                break
            self._print_stat(
                u'Play: %s' % play['play']['name'],
                u'%0.2fs' % play_duration.total_seconds()
            )
            for task in play['tasks']:
                task_duration = task['task']['duration']['end'] - task['task']['duration']['start']
                self._print_stat(
                    u'    %s' % task['task']['name'],
                    u'%0.2fs' % task_duration.total_seconds(),
                    char='-'
                )
                if self._show_host_timings:
                    for host, data in task['hosts'].items():
                        host_duration = data['_duration']['end'] - data['_duration']['start']
                        self._print_stat(
                            u'        %s' % host,
                            u'%0.2fs' % host_duration.total_seconds(),
                            char='.'
                        )
            self._display.display(u'')

    def _record_task_result(self, on_info, result, **kwargs):
        """This function is used as a partial to add failed/skipped info in a single method"""
        end_time = current_time()
        host = result._host
        task = result._task
        task_result = result._result.copy()
        task_result.update(on_info)
        task_result['action'] = task.action
        self.results[-1]['tasks'][-1]['hosts'][host.name] = task_result
        self.results[-1]['tasks'][-1]['hosts'][host.name]['_duration'] = {
            'start': self._host_start[host.name],
            'end': end_time
        }
        self.results[-1]['tasks'][-1]['task']['duration']['end'] = end_time
        self.results[-1]['play']['duration']['end'] = end_time

    def __getattribute__(self, name):
        """Return ``_record_task_result`` partial with a dict containing skipped/failed if necessary"""
        if name not in ('v2_runner_on_ok', 'v2_runner_on_failed', 'v2_runner_on_unreachable', 'v2_runner_on_skipped'):
            return object.__getattribute__(self, name)

        on = name.rsplit('_', 1)[1]

        on_info = {}
        if on in ('failed', 'skipped'):
            on_info[on] = True

        return partial(self._record_task_result, on_info)
