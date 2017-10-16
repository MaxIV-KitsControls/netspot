#!/usr/bin/python -tt

"""Ansible runner."""

import signal
import threading
import Queue
import time
import taskdb
import ansible_api

from ansible.errors import AnsibleError
import netspot_settings

PLAYBOOK_PATH = netspot_settings.PLAYBOOK_PATH
SLEEP_TIMER = netspot_settings.SLEEP_TIMER

class TaskProcessor(object):
  """Task processor."""

  def __init__(self, num_threads=3):
    self.shutting_down = False
    self.setup_signals()
    self.num_threads = num_threads
    self.task_queue = Queue.Queue()

    self.setup_threads()

  def shutdown(self, signum, frame):
    """Shutdown."""
    self.shutting_down = True
    self.task_queue = Queue.Queue()  # Reset the input queue
    print('Shutdown in progress - waiting for background threads to '
          'terminate')

  def setup_signals(self):
    """Setup signals."""

    signal.signal(signal.SIGINT, self.shutdown)
    signal.signal(signal.SIGTERM, self.shutdown)

  def setup_threads(self):
    """Setup threads."""

    for num in range(self.num_threads):
      thread = threading.Thread(target=self.task_handler, args=[self.task_queue])
      thread.start()

  def run(self):
    """Run."""

    while not self.shutting_down:
      tasks = self.get_tasks()

      if not tasks:
        print 'No tasks to process.'
        time.sleep(SLEEP_TIMER)
        continue

      for task in tasks:
        self.task_queue.put(task)
      time.sleep(SLEEP_TIMER)

  def task_handler(self, task_queue):
    """Fetch tasks and start to process them."""

    while not self.shutting_down:

      try:
        task = task_queue.get(block=True, timeout=2)

        # Update the database
        with taskdb.TaskDB() as db_conn:

          # Mark task as active
          db_conn.update_status(task.id, taskdb.Task.STATUS_CODES['ACTIVE'])

          # Process task
          status = self.process_task(task)

          # Save result and mark task as processed
          db_conn.delete_inventory_data(task.id)
          db_conn.update_status(task.id, status)

      except Queue.Empty:
        pass

  def get_tasks(self):
    """Get queued tasks."""

    with taskdb.TaskDB() as db_conn:
      tasks = db_conn.get_tasks_by_status(taskdb.Task.STATUS_CODES['QUEUED'])
    return tasks


  def process_task(self, task):
    """Process task.

    Args:
      task: Task object

    Return:
      status: integer, one of taskdb.Task.STATUS_CODES processed codes
    """

    # Create Ansible runner object
    runner = ansible_api.Runner(username=task.username,
                                playbook=PLAYBOOK_PATH + task.playbook,
                                private_key_file=None,
                                inventory_data=eval(task.inventory_data),
                                extra_vars=eval(task.extra_vars),
                                become_pass=task.become_pass,
                                verbosity=task.verbosity,
                                search_filter=task.hosts)

    try:
      run_status = runner.run()

      if run_status['failures']:
        return taskdb.Task.STATUS_CODES['PROCESSED_FAILURES']
      else:
        return taskdb.Task.STATUS_CODES['PROCESSED']

    except AnsibleError:
      return taskdb.Task.STATUS_CODES['ANSIBLE_ERROR']

def main():
  """Main."""

  task_processor = TaskProcessor()
  task_processor.run()

if __name__ == '__main__':
  main()
