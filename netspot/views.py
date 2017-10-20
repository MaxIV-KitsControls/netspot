"""NetSPOT views."""

import datetime
import helpers
import netspot_settings

from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from .models import ConfigurationTemplate, Category
from .lib.spotmax import netspot
from .lib.spotmax import spotmax

def auth_and_login(request):
  """Authenticate and login user."""

  # Get username and password
  username = request.POST.get('username', None)
  password = request.POST.get('password', None)

  if not username:
    return login_form(request, message="Something went wrong. Please try again.")

  # Authenticate user
  user = authenticate(request, username=username, password=password)

  if user:
    # All users are superusers
    user.is_superuser = True
    user.save()

    # Login in user and return index
    login(request, user)
    return index(request)

  # Return login form if user is not logged in
  return login_form(request, message="Incorrect username or password.")

def login_form(request, message=None):
  """Login form."""

  return render(
      request,
      'login.htm',
      context={'message': message},
  )

def logout_user(request):
  """Log out user and send to login page."""
  logout(request)

  return render(
      request,
      'login.htm',
      context={},
  )

@login_required
def index(request):
  """Index."""

  # Statistics
  num_groups = spotmax.SPOTGroup().count()
  num_assets = netspot.NetSPOT().count()
  num_interfaces = netspot.NetSPOT().count_interfaces()

  # Return
  return render(
      request,
      'index.htm',
      context={'num_assets': num_assets,
               'num_interfaces': num_interfaces,
               'num_groups': num_groups},
  )

@login_required
def addasset(request):
  """Add asset form."""

  return render(
      request,
      'addasset.htm',
      context={},
  )

@login_required
def addgroup(request):
  """Add group form."""

  return render(
      request,
      'addgroup.htm',
      context={},
  )

@login_required
def addvariable(request):
  """Add varaible to a given asset."""

  # Get data
  name = request.POST.get('name', None)
  variable = request.POST.get('variable', None)
  value = request.POST.get('value', None)
  target = request.POST.get('target', None)

  if name and variable and value and target:
    # Construct variable
    variable = '%s:%s' % (variable, value)

    inventory = None
    # Get correct inventory
    if target == 'asset':
      inventory = netspot.NetSPOT()
    elif target == 'group':
      inventory = spotmax.SPOTGroup()

    # Add variable
    if inventory:
      result = inventory.add_variable(target, name, variable)
      if result:
        message = 'Variable added.'
      else:
        message = '%s does not exist.' % target
  else:
    message = 'All fields are required.'

  if target == 'asset':
    return asset(request, name, message)
  elif target == 'group':
    return group(request, name, message)

@login_required
def asset(request, asset_name, message=None):
  """Get detail about a given asset."""

  # Get asset
  inventory = netspot.NetSPOT()
  asset_details = inventory.search(asset_name, key='asset')[0]

  # Get user variables if any
  try:
    variables = asset_details['variables']
  except (IndexError, KeyError):
    variables = []

  # Format uptime
  if asset_details.get('uptime'):
    asset_details['uptime'] = str(datetime.timedelta(seconds=asset_details['uptime']))

  # Get asset interfaces if any
  try:
    interfaces = sorted(asset_details['interfaces'], key=lambda k: k['interface'])
  except (IndexError, KeyError):
    interfaces = []

  # Port deployments
  try:
    category = Category.objects.get(name=netspot_settings.PORT_TEMPLATES)
    port_templates = ConfigurationTemplate.objects.filter(category=category).order_by('-name')
  except ObjectDoesNotExist:
    port_templates = []

  return render(
      request,
      'asset.htm',
      context={'name': asset_details['asset'],
               'asset': asset_details,
               'interfaces': interfaces,
               'message': message,
               'variables': variables,
               'port_templates': port_templates,
               'variable_type': 'asset'},
  )

@login_required
def assets(request, page=1):
  """Lists all assets."""

  # Pagination
  page = int(page)
  limit = 50

  # Previous page
  if page >= 2:
    prev_page = page - 1
    no_prev = False
  else:
    prev_page = 1
    no_prev = True

  # Search
  inventory = netspot.NetSPOT()
  result = inventory.search('', key='asset', limit=limit, page=page)

  # Next page
  if result.count(True) == limit:
    next_page = page + 1
    no_next = False
  else:
    next_page = page
    no_next = True

  return render(
      request,
      'assets.htm',
      context={'assets': result,
               'filter': '',
               'showing_result': '%s - %s' % (limit*(page-1), limit*(page)),
               'prev_page': prev_page,
               'next_page': next_page,
               'no_prev': no_prev,
               'no_next': no_next},
  )

@login_required
def deleteasset(request, asset_name):
  """Delete asset."""

  inventory = netspot.NetSPOT()
  inventory.delete(asset_name, key='asset')

  return assets(request)

@login_required
def deletegroup(request, group_name):
  """Delete group."""

  inventory = spotmax.SPOTGroup()
  inventory.delete(group_name, key='group')

  return groups(request)

@login_required
def deletevariable(request, variable, asset_name=None, group_name=None):
  """Delete variable."""

  if asset_name:
    name = asset_name
    target = 'asset'
    inventory = netspot.NetSPOT()
  elif group_name:
    name = group_name
    target = 'group'
    inventory = spotmax.SPOTGroup()

  if inventory.delete_variable(name, variable, target):
    message = 'Variable deleted.'
  else:
    message = 'Failed to delete variable.'

  if asset_name:
    return asset(request, name, message)
  elif group_name:
    return group(request, name, message)

@login_required
def group(request, group_name, message=None):
  """Get data for a given group."""

  # Get group data
  inventory = spotmax.SPOTGroup()
  group_data = inventory.search(group_name, key='group')[0]

  # Get assets in group
  inventory_groups = netspot.NetSPOT()
  result = inventory_groups.search('groups:%s' % group_name, key='group')
  num_assets = result.count()

  # Get user variables if any
  try:
    variables = group_data['variables']
  except (IndexError, KeyError):
    variables = []

  return render(
      request,
      'group.htm',
      context={'name': group_data['group'],
               'group': group_data,
               'message': message,
               'assets': result,
               'num_assets': num_assets,
               'variables': variables,
               'variable_type': 'group'},
  )

@login_required
def groups(request):
  """All grousp."""

  inventory = spotmax.SPOTGroup()
  result = inventory.search('', key='group')

  return render(
      request,
      'groups.htm',
      context={'groups':result},
  )

@login_required
def insertasset(request):
  """Insert asset in database."""

  # Get data
  asset_name = request.POST.get('asset', None)
  loopback = request.POST.get('loopback', None)
  group_list = request.POST.get('groups', None)
  username = request.POST.get('username', None)
  password = request.POST.get('password', None)

  # Login to asset and get asset data
  device = netspot.Asset(asset_name, loopback, group_list, username, password, None)

  # Add to inventory
  inventory = netspot.NetSPOT()
  try:
    inventory.add_new_asset(device)
    message = 'Asset added!'
  except SystemExit:
    message = ('Unable to connect to device. Please check reachability, '
               'username/password and that NETCONF is enabled.')

  return render(
      request,
      'addasset.htm',
      context={'message': message},
  )

@login_required
def insertgroup(request):
  """Insert group in database."""

  # Get data
  group_name = request.POST.get('group', None)

  # Add to inventory
  inventory = spotmax.SPOTGroup()
  inventory.add_group(group_name)
  message = 'Group added!'

  return render(
      request,
      'addgroup.htm',
      context={'message': message},
  )

@login_required
def search(request):
  """Search."""

  # Get search term
  find = helpers.get_search_term(request)

  # Do the actual seach
  inventory = netspot.NetSPOT()
  result = inventory.search(find, key='asset')

  return render(
      request,
      'assets.htm',
      context={'assets': result, 'filter': find},
  )
