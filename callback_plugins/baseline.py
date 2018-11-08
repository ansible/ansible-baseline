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
        description: This adds host timings per task
        default: True
        env:
          - name: BASELINE_SHOW_HOST_TIMINGS
        ini:
          - key: show_host_timings
            section: baseline
        type: bool
      display_recap:
        description: Controls whether the recap is printed at the end, useful if you will automatically
                     process the output files
        env:
          - name: BASELINE_DISPLAY_RECAP
        ini:
          - key: display_recap
            section: baseline
        type: bool
        default: true
      write_json:
        description: Writes output to a JSON file
        default: False
        env:
          - name: BASELINE_WRITE_JSON
        ini:
          - key: write_json
            section: baseline
        type: bool
      json_file:
        description: Path to JSON file for use with "write_json"
        default: /tmp/baseline.json
        env:
          - name: BASELINE_JSON_FILE
        ini:
          - key: json_file
            section: baseline
        type: path
'''

import datetime
import json

from ansible.plugins.callback import CallbackBase

try:
    from ansible.executor.process.worker import WorkerProcess
except ImportError:
    # If this fails, it just means we are on a version where we don't need it
    pass


class _JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime.datetime):
            return o.isoformat()
        return super(_JSONEncoder, self).default(o)


def current_time():
    return datetime.datetime.utcnow()


class CallbackModule(CallbackBase):
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'aggregate'
    CALLBACK_NAME = 'baseline'

    def __init__(self, display=None):
        super(CallbackModule, self).__init__(display)
        self._results = []
        self._host_start = {}
        self._show_host_timings = True
        self._write_json = False
        self._json_file = '/tmp/baseline.json'
        self._display_recap = True

        self._play = None
        self._task = None

        try:
            CallbackBase.v2_runner_on_start
        except AttributeError:
            # Ansible<2.8
            WorkerProcess.__init__ = self._infect_worker(WorkerProcess.__init__)

    def _infect_worker(self, func):
        """Intended to wrap ``WorkerProcess.__init__`` and log the start time for a host

        Please don't do this elsewhere, it's bad enough I'm doing it here.

        Used on Ansible<2.8
        """
        def inner(*args):
            host = args[3]
            self._host_start[host.name] = current_time()
            func(*args)
        return inner

    def _new_play(self, play):
        self._play = {
            'play': {
                'name': play.get_name(),
                'id': str(play._uuid),
                'duration': {
                    'start': current_time()
                }
            },
            'tasks': []
        }
        return self._play

    def _new_task(self, task):
        self._host_start = {}
        self._task = {
            'task': {
                'name': task.get_name(),
                'id': str(task._uuid),
                'duration': {
                    'start': current_time()
                }
            },
            'hosts': {}
        }
        return self._task

    def set_options(self, *args, **kwargs):
        super(CallbackModule, self).set_options(*args, **kwargs)
        try:
            self._show_host_timings = self.get_option('show_host_timings')
            self._write_json = self.get_option('write_json')
            self._json_file = self.get_option('json_file')
            self._display_recap = self.get_option('display_recap')
        except TypeError:
            # Ansible 2.4
            self._show_host_timings = self._plugin_options['show_host_timings']
            self._write_json = self._plugin_options['write_json']
            self._json_file = self._plugin_options['json_file']
            self._display_recap = self._plugin_options['display_recap']

    def v2_playbook_on_play_start(self, play):
        self._results.append(self._new_play(play))

    def v2_playbook_on_task_start(self, task, is_conditional):
        self._play['tasks'].append(self._new_task(task))

    def v2_playbook_on_handler_task_start(self, task):
        self._play['tasks'].append(self._new_task(task))

    def _print_stat(self, start, end, char=u'*'):
        columns = self._display.columns
        fill = columns - len(start) - len(end) - 2
        self._display.display('%s %s %s' % (start, char * fill, end))

    @staticmethod
    def _host_start_offset(host_data):
        host, data = host_data
        return (data['offset']['end'] - data['offset']['start']).total_seconds()

    def v2_playbook_on_stats(self, stats):
        """Display info about playbook statistics"""

        if self._write_json:
            with open(self._json_file, 'w+') as f:
                json.dump(self._results, f, indent=4, cls=_JSONEncoder)

        if not self._display_recap:
            return

        for play in self._results:
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
                    char=u'-'
                )
                if self._show_host_timings:
                    for host, data in sorted(task['hosts'].items(), key=self._host_start_offset):
                        host_wait = (data['offset']['end'] - data['offset']['start']).total_seconds()
                        host_duration = (data['duration']['end'] - data['duration']['start']).total_seconds()
                        self._print_stat(
                            u'        %s' % host,
                            u'%0.2fs / %0.2fs' % (host_duration, host_wait),
                            char=u'.'
                        )
            self._display.display(u'')

    def v2_runner_on_start(self, host, task):
        self._host_start[host.name] = current_time()

    def v2_runner_on_ok(self, result, **kwargs):
        """Note: Do as few calculations in here, and limit stored data to prevent excessive
        observer effect
        """
        end_time = current_time()
        host = result._host.name
        self._task['hosts'][host] = {
            'duration': {
                'start': self._host_start[host],
                'end': end_time
            },
            'offset': {
                'start': self._task['task']['duration']['start'],
                'end': self._host_start[host]
            }
        }
        self._task['task']['duration']['end'] = end_time
        self._play['play']['duration']['end'] = end_time

    v2_runner_on_failed = v2_runner_on_unreachable = v2_runner_on_skipped = v2_runner_on_ok
