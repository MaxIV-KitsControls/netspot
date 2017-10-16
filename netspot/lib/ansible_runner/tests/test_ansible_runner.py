#!/usr/bin/python -tt
"""TaskProcessor tests

  Run: python -m unittest tests.test_ansible_runner

"""

import mock
import unittest

import ansible_runner
import taskdb

from datetime import datetime
from ansible.errors import AnsibleError


class MockRunner(object):
  def __init__(self,
               username=None,
               playbook=None,
               private_key_file=None,
               inventory_data=None,
               extra_vars=None,
               become_pass=None,
               verbosity=None,
               search_filter=None):

    self.playbook = playbook
    self.return_value = {'failures': 0}

  def run(self):
    if 'yml' in self.playbook:
      return self.return_value
    else:
      raise AnsibleError

class TestTaskProcessor(unittest.TestCase):
  def setUp(self):
    ansible_runner.ansible_api.Runner = MockRunner
    self.tp = ansible_runner.TaskProcessor(num_threads=0)

  def test_process_task(self):
    # Successfull processing
    task = taskdb.Task(1,
                       status=taskdb.Task.STATUS_CODES['ACTIVE'],
                       date=datetime.now(),
                       username='mock_user',
                       playbook='mock_play.yml',
                       inventory_data='{}',
                       extra_vars='{}',
                       become_pass=None,
                       verbosity=0,
                       hosts='test_host')

    status = self.tp.process_task(task)
    self.assertEqual(status, taskdb.Task.STATUS_CODES['PROCESSED'])

    # Test Ansible error
    task = taskdb.Task(1,
                       status=taskdb.Task.STATUS_CODES['ACTIVE'],
                       date=datetime.now(),
                       username='mock_user',
                       playbook='mock_play',
                       inventory_data='{}',
                       extra_vars='{}',
                       become_pass=None,
                       verbosity=0,
                       hosts='test_host')

    status = self.tp.process_task(task)
    self.assertEqual(status, taskdb.Task.STATUS_CODES['ANSIBLE_ERROR'])


if __name__ == '__main__':
  unittest.main()
