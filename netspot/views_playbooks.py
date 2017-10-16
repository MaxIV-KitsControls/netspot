"""NetSPOT MAC views."""

from collections import defaultdict

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.conf import settings
from .models import Playbook, PlaybookVariable
from .lib.spotmax import netspot, nsinv
from .lib.ansible_runner import taskdb
from netspot.views_templify import template_input

import netspot.helpers as helpers


class PlaybookRun(object):
  """Ansible playbook run class."""

  def __init__(self,
               username=None,
               ansible_username=None,
               ansible_password=None,
               playbook=None,
               search_filter=None,
               extra_vars=None):

    # Playbook
    self.playbook = playbook
    self.playbook_path = playbook.playbook_file

    # Username of the user running the playbook
    self.username = username

    # Ansible playbook username / password
    self.ansible_username = ansible_username
    self.ansible_password = ansible_password

    # Extra vars
    self.extra_vars = defaultdict()
    for var in extra_vars:
      self.extra_vars[var] = extra_vars[var][0]

    if ansible_username:
      self.extra_vars['username'] = ansible_username
      self.extra_vars['password'] = ansible_password

    self.search_filter = search_filter

    # Ansible command to run
    self.cmd = None

    # Output and run status of the Ansible run
    self.run_output = ''
    self.run_status = None

    # Colorized output
    self.color_output = ''

  def run(self):
    """Run playbook."""

    # Get inventory
    inventory = nsinv.AnsibleInventory(attribute=self.search_filter, json_output=False)

    # Add Ansible job
    with taskdb.TaskDB() as tasks:
      task = taskdb.Task(id=None,
                         status=1,
                         username=self.username,
                         playbook=self.playbook_path,
                         inventory_data=str(dict(inventory)),
                         extra_vars=str(dict(self.extra_vars)),
                         become_pass='',
                         verbosity=0,
                         hosts=self.search_filter)

      tasks.add_task(task)

@login_required
def playbooks(request):
  """Playbooks view."""

  # Get playbooks
  all_playbooks = Playbook.objects.all()

  return render(
      request,
      'playbooks.htm',
      context={'playbooks': all_playbooks},
  )

@login_required
def deployport(request):
  """Deploy port shortcut."""

  template_id = request.POST.get('template_id', None)

  return template_input(request, template_id)

@login_required
def playbookredirector(request):
  """Redirect request based on playbook name."""

  # Get input
  playbook_id = request.POST.get('playbook', None)
  config_filename = request.POST.get('config_filename', None)

  # Return playbook input view
  if playbook_id and config_filename:
    config_filepath = settings.TEMP_DIRECTORY + config_filename
    return playbook_input(request, playbook_id=playbook_id, config_file=config_filepath)
  else:
    return playbooks(request)

@login_required
def playbook_input(request, playbook_id, config_file=None, template=None):
  """Playbook input view."""

  # Get playbook
  playbook = Playbook.objects.get(pk=playbook_id)

  # Get username
  user = str(request.user)

  # Check user permissions
  if user not in playbook.permissions.users:
    return playbooks(request)

  # Get asset name if provided
  asset_name = request.POST.get('asset_name', None)

  # Get Assets
  if playbook.asset_filter != '*':
    inventory = netspot.NetSPOT()
    assets = inventory.search(playbook.asset_filter, key='asset')
  else:
    assets = None

  # Get config if confgi_file is provided
  config = None
  if config_file:
    with open(config_file, 'r') as file_handle:
      config = file_handle.read().strip()

  variables = PlaybookVariable.objects.filter(playbook=playbook)

  return render(
      request,
      'playbook.htm',
      context={'playbook': playbook.name,
               'playbook_id': playbook.id,
               'assets': assets,
               'asset_name': asset_name,
               'asset_filter': playbook.asset_filter,
               'user_auth': playbook.user_auth,
               'inputs': variables,
               'config_file': config_file,
               'config': config,
               'template': template,
               'description': playbook.description},
  )

@login_required
def playbook_log(request):
  """Retrieve log entries."""

  log = netspot.NetSPOTLog()

  log_entries = log.get_log_entries(50)

  # Convert '_id' to string and remove '_' from the key
  logs = list()
  for log in log_entries:
    log['id'] = str(log['_id'])
    del log['_id']
    logs.append(log)

  return render(
      request,
      'playbooklog.htm',
      context={'log_entries': logs},
  )

@login_required
def playbook_log_details(request, log_id):
  """Get log entry details."""

  log = netspot.NetSPOTLog()

  log_entry = log.get_log_entry(log_id)

  return render(
      request,
      'logdetails.htm',
      context={'log_id': log_id,
               'log_entry': log_entry,
               'color_output': helpers.colorize_output(log_entry['output'])},
  )

@login_required
def run_playbook(request):
  """Run playbook."""

  # Get data from POST
  playbook_id = request.POST.get('playbook_id', '')
  asset_filter = request.POST.getlist('filter', '')
  ansible_username = request.POST.get('ansible_username', None)
  ansible_password = request.POST.get('ansible_password', None)

  # Convert list to comma separated string
  asset_filter = ','.join(asset_filter)

  # Remove unnecessary POST data
  data = dict(request.POST)
  try:
    del data['playbook_id']
    del data['filter']
    del data['csrfmiddlewaretoken']
    del data['ansible_username']
    del data['ansible_password']
  except KeyError:
    pass

  # Get playbook object
  playbook = Playbook.objects.get(pk=playbook_id)

  # Run playbook
  pbr = PlaybookRun(request.user.username,
                    ansible_username,
                    ansible_password,
                    playbook,
                    asset_filter,
                    extra_vars=data)
  pbr.run()

  return ansibletasks(request)

# Ansible Job Queue
@login_required
def ansibletasks(request):
  """View for the Ansible job queue."""

  active_tasks = None
  queued_tasks = None
  processed_tasks = None
  error_message = None

  # Get queued tasks
  try:
    with taskdb.TaskDB() as tasks:
      active_tasks = tasks.get_tasks_by_status(taskdb.Task.STATUS_CODES['ACTIVE'], limit=10)
      queued_tasks = tasks.get_tasks_by_status(taskdb.Task.STATUS_CODES['QUEUED'], limit=10)
      processed_tasks = tasks.get_processed_tasks(limit=10)
  except taskdb.DatabaseMissing:
    error_message = 'Database is either missing or damaged.'

  return render(
      request,
      'ansibletasks.htm',
      context={'error_message': error_message,
               'active_tasks': active_tasks,
               'processed_tasks': processed_tasks,
               'queued_tasks': queued_tasks}
  )

@login_required
def taskdetails(request, task_id):
  """Details Ansible job task."""

  with taskdb.TaskDB() as tasks:
    task = tasks.get_task(task_id)

  return render(
      request,
      'taskdetails.htm',
      context={'task': task}
  )

@login_required
def deletetask(request, task_id):
  """Details Ansible job task."""

  with taskdb.TaskDB() as tasks:
    task = tasks.delete_task(task_id)

  return ansibletasks(request)

@login_required
def retry_task(request, log_id):
  """Re-add a task to the queue again."""

  log = netspot.NetSPOTLog()

  # Get log entry and playbook
  log_entry = log.get_log_entry(log_id)
  playbook = Playbook.objects.get(playbook_file=log_entry['playbook'])

  # Create extra vars
  extra_vars = dict()
  for variable in log_entry['arguments']:
    extra_vars[variable] = [log_entry['arguments'][variable]]

  # Run playbook
  pbr = PlaybookRun(username=request.user.username,
                    ansible_username=None,
                    ansible_password=None,
                    playbook=playbook,
                    search_filter=log_entry['filter'],
                    extra_vars=extra_vars)
  pbr.run()

  return ansibletasks(request)
