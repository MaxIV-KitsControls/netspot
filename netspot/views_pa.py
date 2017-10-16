# -*- coding: utf-8 -*-

"""Views."""

from __future__ import unicode_literals

import helpers
import cdb_helper
import views_playbooks
import views_templify
import ts_lib

from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from .models import ConfigurationTemplate, Category
from .lib.spotmax import netspot


@login_required
def pa_port(request):
  """Port view."""

  # Get port templates
  try:
    category = Category.objects.get(name='Network ports')
    port_templates = ConfigurationTemplate.objects.filter(category=category).order_by('-name')
  except ObjectDoesNotExist:
    port_templates = []

  return render(
      request,
      'pa/port.htm',
      context={'port_templates': port_templates},
  )

@login_required
def pa_ts_port(request):
  """Port troubleshooter form."""

  return render(
      request,
      'pa/ts_port.htm',
      context={},
  )

@login_required
def dhcp_search(request):
  """Search DHCP logs."""

  search = request.POST.get('search', None)
  network = request.POST.get('network', None)

  if search and network:
    dhcp_server = helpers.get_dhcp_server(network=network)
    dhcp_logs, dhcp_error = helpers.search_dhcp_log(search, dhcp_server)

    # Return a search form
    return render(
        request,
        'pa/dhcpsearchresult.htm',
        context={'search': search,
                 'network': network,
                 'dhcp_logs': dhcp_logs,
                 'dhcp_error': dhcp_error},
    )

  # Return a search form
  return render(request, 'pa/dhcpsearch.htm', context={})

@login_required
def pa_troubleshoot(request):
  """Port troubleshooter form."""

  error_message = None
  interface = {}
  asset = None
  interface_name = None
  loopback = None
  ssh_key = None

  outlet = request.POST.get('outlet', None)

  # Get cable path
  cable_path = cdb_helper.get_cable_path(outlet)

  try:
    # Get interface
    interface, beamline = cdb_helper.get_interface_beamline(cable_path)
    asset = interface.split(':')[0]
    interface_name = interface.split(':')[1]

    # Check if user should have access to this beamline
    helpers.check_beamline_access(request, beamline)

    # Get asset
    asset_details = netspot.NetSPOT().search(asset, key='asset')

    # Get group SSH key file
    group_name = asset_details[0]['groups'][0]
    loopback = asset_details[0]['loopback']
    group_details = netspot.NetSPOTGroup().search(group_name, key='group')

    # Find SSH key
    for var in group_details[0]['variables']:
      if var.get(u'ssh_keyfile'):
        ssh_key = var.get(u'ssh_keyfile').encode('ascii', 'ignore')
        break
  except cdb_helper.CablePathEmpty:
    # Outlet input incorrect or cable doesn't exist
    error_message = 'Outlet not found. Incorrect input.'
  except cdb_helper.NoAssetFound:
    # Asset can't be found. Incorrect input.
    error_message = 'No switch found. Incorrect input.'
  except helpers.BeamlineDenied as error:
    # User don't have access to this beamline.
    error_message = error.args[0]

  # Connect and run troubleshooter
  device = ts_lib.TroubleshootDevice(asset, loopback, ssh_key, interface_name)
  device.run()

  # Check for error messages
  if device.error_message:
    error_message = device.error_message


  return render(
      request,
      'pa/ts_port_report.htm',
      context={'outlet': outlet,
               'error': error_message,
               'asset': asset,
               'interface_name': interface_name,
               'lldp': device.lldp,
               'macs': device.macs,
               'mac_address': device.mac_address,
               'dhcp_logs': device.dhcp_logs,
               'dhcp_error': device.dhcp_error,
               'log_messages': device.log_entries,
               'interface': device.interface},
  )

@login_required
def pa_prepare(request):
  """Prepare to deploy view."""

  # Error message
  asset = None
  config = ''
  error_message = None

  # Get input
  outlet = request.POST.get('outlet', None)
  template_id = request.POST.get('template_id', None)
  confirmed = request.POST.get('confirmed', False)
  beamline = None
  interface = None

  try:
    # Get cable path
    cable_path = cdb_helper.get_cable_path(outlet)

    # Get interface and beamline
    interface, beamline = cdb_helper.get_interface_beamline(cable_path)
    asset = interface.split(':')[0]
    interface = interface.split(':')[1]

    # Check if user should have access to this beamline
    helpers.check_beamline_access(request, beamline)

    # Generate configuration
    template = get_object_or_404(ConfigurationTemplate, pk=template_id)
    template_variables = {'interfaces': [interface], 'beamline': beamline}
    file_path, config, error = views_templify.get_config(template_variables, template)

    # Create extra vars
    variables = dict()
    variables['config_file'] = [file_path]
    variables['commit_comment'] = ['PA: %s' % request.user.username]
    variables['update_style'] = ['replace']

    # Run playbook
    pbr = views_playbooks.PlaybookRun(request.user.username,
                                      None,
                                      None,
                                      template.playbook,
                                      asset,
                                      extra_vars=variables)
    if confirmed:
      pbr.run()

  except cdb_helper.CablePathEmpty:
    # Outlet input incorrect or cable doesn't exist
    error_message = 'Outlet not found. Incorrect input.'
  except cdb_helper.NoAssetFound:
    # Asset can't be found. Incorrect input.
    error_message = 'No switch found. Incorrect input.'
  except helpers.BeamlineDenied as error:
    # User don't have access to this beamline.
    error_message = error.args[0]

  return render(
      request,
      'pa/prepare.htm',
      context={'confirmed': confirmed,
               'error_message': error_message,
               'outlet': outlet,
               'beamline': beamline,
               'template_id': template_id,
               'cable_path': cable_path,
               'asset': asset,
               'interfaces': interface,
               'config': config},
  )
