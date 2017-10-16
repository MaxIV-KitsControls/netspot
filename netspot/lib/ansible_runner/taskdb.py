#!/usr/bin/python -tt

"""TaskDB - Interacts with a task DB."""

import os
import sqlite3

from datetime import datetime
import netspot_settings

SCHEMA = ('CREATE TABLE tasks( '
          'id INTEGER PRIMARY KEY, '
          'status INTEGER, '
          'date DATE, '
          'username TEXT, '
          'playbook TEXT, '
          'inventory_data TEXT, '
          'extra_vars TEXT, '
          'become_pass TEXT, '
          'verbosity INTEGER, '
          'hosts TEXT)')


SQL_INSERT = ('''
  INSERT INTO tasks (date, status, username, playbook, inventory_data, extra_vars, become_pass, verbosity, hosts)
  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''')
SQL_DELETE = ('''DELETE FROM tasks WHERE id = ?''')
SQL_SELECT_ONE = ('''SELECT * FROM tasks WHERE id = ? LIMIT 1''')

class Task(object):
  """Task object."""

  STATUS_CODES = {
      'QUEUED': 1,
      'ACTIVE': 2,
      'PROCESSED': 3,
      'PROCESSED_FAILURES': 4,
      'ANSIBLE_ERROR': 5}

  def __init__(self,
               id,
               status=None,
               date=None,
               username=None,
               playbook=None,
               inventory_data=None,
               extra_vars=None,
               become_pass=None,
               verbosity=0,
               hosts=None):

    self.id = id
    self.status = status
    self.date = date
    self.username = username
    self.playbook = playbook
    self.inventory_data = inventory_data
    self.extra_vars = extra_vars
    self.become_pass = become_pass
    self.verbosity = verbosity
    self.hosts = hosts

class DatabaseMissing(Exception):
  """Database file missing."""
  pass

class TaskDB(object):
  """TaskDB."""

  def __init__(self, database=netspot_settings.TASK_DATABASE):
    self.database = database
    self.session = None

  def _open_session(self):
    """Returns a datbase session."""

    if not os.path.isfile(self.database):
      self.setup()

    if not self.session:
      try:
        with sqlite3.connect(self.database) as session:
          self.session = session
      except sqlite3.OperationalError:
        print 'Failed to open database file.'

  def __enter__(self):
    """Open DB session."""
    self._open_session()
    return self

  def __exit__(self, ex_type, ex_value, traceback):
    """Close DB session."""
    if self.session:
      self.session.close()

  def setup(self):
    """Setup queue table."""

    try:
      with sqlite3.connect(self.database) as session:
        session.execute(SCHEMA)
        session.commit()
    except sqlite3.OperationalError:
      raise DatabaseMissing('Database file missing or damaged.')


  def delete_task(self, task_id):
    """Delete task from database.

    Args:
      task_id: integer, task ID
    """

    self.session.execute(SQL_DELETE, [str(task_id)])
    self.session.commit()

  def delete_inventory_data(self, task_id):
    """Delete invenotory data.

    Args:
      task_id: integer, task ID
    """
    sql = ('''
           UPDATE tasks
           SET inventory_data = ''
           WHERE id = %s;
    ''')

    self.session.execute(sql % task_id)
    self.session.commit()

  def get_task(self, task_id):
    """Get and return a task.

    Args:
      task_id: integer, task ID

    Returns:
      task, Task object
    """

    if self.session:
      row = self.session.execute(SQL_SELECT_ONE, str(task_id))

    try:
      task = Task(*row.fetchone())
      return task
    except:
      return None

  def get_tasks_by_status(self, status, limit=1):
    """Returns tasks with status.

    Args:
      status: integer, Task STATUS_CODES
      limit: integer, number of tasks to retrieve

    Returns:
      tasks: list, list of Task objects
    """
    sql = ('''
        SELECT *
        FROM tasks
        WHERE status = %s
        LIMIT %s
    ''')

    tasks = []
    if self.session:
      for row in self.session.execute(sql % (status, limit)):
        task = Task(*row)
        tasks.append(task)

    return tasks

  def get_processed_tasks(self, limit=1):
    """Returns tasks with any processed status.

    Args:
      limit: integer, number of tasks to retrieve

    Returns:
      tasks: list, list of Task objects
    """
    sql = ('''
        SELECT *
        FROM tasks
        WHERE status = %s OR status = %s or status = %s
        ORDER BY date DESC
        LIMIT %s
    ''')

    tasks = []
    if self.session:
      for row in self.session.execute(sql % (Task.STATUS_CODES['PROCESSED'],
                                             Task.STATUS_CODES['PROCESSED_FAILURES'],
                                             Task.STATUS_CODES['ANSIBLE_ERROR'],
                                             limit)):
        task = Task(*row)
        tasks.append(task)

    return tasks

  def add_task(self, task):
    """Insert new task in database.

    Args:
      task: Task object
    """

    self.session.execute(SQL_INSERT, (datetime.now(),
                                      task.status,
                                      task.username,
                                      task.playbook,
                                      task.inventory_data,
                                      task.extra_vars,
                                      task.become_pass,
                                      task.verbosity,
                                      task.hosts))
    self.session.commit()

  def print_tasks(self, limit=10):
    """Print tasks."""

    for row in self.session.execute('SELECT * FROM tasks LIMIT %s' % limit):
      print row

  def update_status(self, task_id, status):
    """Updates status for a given task.

    Args:
      task_id: integer, task ID
      status: integer, Task STATUS_CODES
    """

    sql = ('''
            UPDATE tasks
            SET status="%s", date="%s"
            WHERE id=%s
    ''')

    self.session.execute(sql % (status, datetime.now(), task_id))
    self.session.commit()

def main():
  """Main."""

  with TaskDB() as taskdb:
    taskdb.print_tasks()

if __name__ == '__main__':
  main()
