#!/usr/bin/python -tt

"""Ansible CallBackModule to log output."""

# pylint: disable=W0212

from datetime import datetime
from ansible.plugins.callback import CallbackBase

try:
  from spotmax import spotmax
except ImportError:
  pass

class PlayLogger(object):
  """Store log output in a single object."""

  def __init__(self):
    self.log = ''
    self.runtime = 0

  def append(self, log_line):
    """append to log"""

    self.log += log_line+"\n\n"

class CallbackModule(CallbackBase):
  """Format Ansible output."""

  CALLBACK_VERSION = 2.0
  CALLBACK_TYPE = 'stored'
  CALLBACK_NAME = 'database'

  def __init__(self):
    super(CallbackModule, self).__init__()
    self.logger = PlayLogger()
    self.start_time = datetime.now()

  def v2_runner_on_failed(self, result, ignore_errors=False):
    """Failed host."""

    delegated_vars = result._result.get('_ansible_delegated_vars', None)

    # Catch an exception
    # This may never be called because default handler deletes
    # the exception, since Ansible thinks it knows better
    if 'exception' in result._result:
      # Extract the error message and log it
      error = result._result['exception'].strip().split('\n')[-1]
      self.logger.append(error)

      # Remove the exception from the result so it's not shown every time
      del result._result['exception']

    # Else log the reason for the failure
    if result._task.loop and 'results' in result._result:
      self._process_items(result)  # item_on_failed, item_on_skipped, item_on_ok
    else:
      if delegated_vars:
        self.logger.append("fatal: [%s -> %s]: FAILED! => %s" % (
            result._host.get_name(),
            delegated_vars['ansible_host'],
            self._dump_results(result._result)))
      else:
        self.logger.append("fatal: [%s]: FAILED! => %s" % (result._host.get_name(),
                                                           self._dump_results(result._result)))

  def v2_runner_on_ok(self, result):
    """OK host."""
    self._clean_results(result._result, result._task.action)
    delegated_vars = result._result.get('_ansible_delegated_vars', None)
    if result._task.action == 'include':
      return
    elif result._result.get('changed', False):
      if delegated_vars:
        msg = "changed: [%s -> %s]" % (result._host.get_name(), delegated_vars['ansible_host'])
      else:
        msg = "changed: [%s]" % result._host.get_name()
    else:
      if delegated_vars:
        msg = "ok: [%s -> %s]" % (result._host.get_name(), delegated_vars['ansible_host'])
      else:
        msg = "ok: [%s]" % result._host.get_name()

        if 'ansible_facts' not in result._result:
          msg += '\n%s' % self._dump_results(result._result)

    if result._task.loop and 'results' in result._result:
      self._process_items(result)  # item_on_failed, item_on_skipped, item_on_ok
    else:
      self.logger.append(msg)

  def v2_runner_on_skipped(self, result):
    """Skipped host."""

    if result._task.loop and 'results' in result._result:
      self._process_items(result)  # item_on_failed, item_on_skipped, item_on_ok
    else:
      msg = "skipping: [%s]" % result._host.get_name()
      self.logger.append(msg)

  def v2_runner_on_unreachable(self, result):
    """Unreachable host."""

    delegated_vars = result._result.get('_ansible_delegated_vars', None)
    if delegated_vars:
      self.logger.append("fatal: [%s -> %s]: UNREACHABLE! => %s" % (
          result._host.get_name(),
          delegated_vars['ansible_host'],
          self._dump_results(result._result)))
    else:
      self.logger.append("fatal: [%s]: UNREACHABLE! => %s" % (result._host.get_name(),
                                                              self._dump_results(result._result)))

  def v2_runner_on_no_hosts(self, task):
    self.logger.append("skipping: no hosts matched")

  def v2_playbook_on_task_start(self, task, is_conditional):
    self.logger.append("TASK [%s]" % task.get_name().strip())

  def v2_playbook_on_play_start(self, play):
    name = play.get_name().strip()
    if not name:
      msg = "PLAY"
    else:
      msg = "PLAY [%s]" % name

    self.logger.append(msg)

  def v2_playbook_item_on_ok(self, result):
    """OK item."""

    delegated_vars = result._result.get('_ansible_delegated_vars', None)
    if result._task.action == 'include':
      return
    elif result._result.get('changed', False):
      if delegated_vars:
        msg = "changed: [%s -> %s]" % (result._host.get_name(), delegated_vars['ansible_host'])
      else:
        msg = "changed: [%s]" % result._host.get_name()
    else:
      if delegated_vars:
        msg = "ok: [%s -> %s]" % (result._host.get_name(), delegated_vars['ansible_host'])
      else:
        msg = "ok: [%s]" % result._host.get_name()

    msg += " => (item=%s)" % (result._result['item'])

    self.logger.append(msg)

  def v2_playbook_item_on_failed(self, result):
    """Failed item."""

    delegated_vars = result._result.get('_ansible_delegated_vars', None)
    if 'exception' in result._result:
      # Extract the error message and log it
      error = result._result['exception'].strip().split('\n')[-1]
      self.logger.append(error)

      # Remove the exception from the result so it's not shown every time
      del result._result['exception']

    if delegated_vars:
      self.logger.append("failed: [%s -> %s] => (item=%s) => %s" % (
          result._host.get_name(),
          delegated_vars['ansible_host'],
          result._result['item'],
          self._dump_results(result._result)))
    else:
      self.logger.append("failed: [%s] => (item=%s) => %s" % (result._host.get_name(),
                                                              result._result['item'],
                                                              self._dump_results(result._result)))

  def v2_playbook_item_on_skipped(self, result):
    """Skipped item."""

    msg = "skipping: [%s] => (item=%s) " % (result._host.get_name(), result._result['item'])
    self.logger.append(msg)

  def v2_playbook_on_stats(self, stats):
    """Recap."""

    run_time = datetime.now() - self.start_time
    self.logger.runtime = run_time.seconds  # returns an int, unlike run_time.total_seconds()

    hosts = sorted(stats.processed.keys())
    for host in hosts:
      host_status = stats.summarize(host)

      msg = "PLAY RECAP [%s] : %s %s %s %s %s" % (
          host,
          "ok: %s" % (host_status['ok']),
          "changed: %s" % (host_status['changed']),
          "unreachable: %s" % (host_status['unreachable']),
          "skipped: %s" % (host_status['skipped']),
          "failed: %s" % (host_status['failures']),
      )

      self.logger.append(msg)

  def record_logs(self,
                  username,
                  success=False,
                  extra_vars=None,
                  playbook=None,
                  search_filter=None):
    """Log Ansible run.

    Args:
      username: string, username running playbook
      success: boolean, run success
      extra_vars: dict, ansible extra variables
      playbook: string, playbook file name
      search_filter: string, hosts for the playbook
    """

    log = spotmax.SPOTLog()

    # Remove password
    try:
      del extra_vars['password']
    except KeyError:
      pass

    log.log(username=username,
            playbook=playbook.split('/',)[-1],
            search_filter=search_filter,
            arguments=extra_vars,
            runtime=self.logger.runtime,
            success=success,
            output=self.logger.log)
