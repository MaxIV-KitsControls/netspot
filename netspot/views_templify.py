# -*- coding: utf-8 -*-

"""Views."""

from __future__ import unicode_literals

import os
import uuid

from collections import defaultdict

from django.template import Context, Template, TemplateSyntaxError
from django.conf import settings
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, Http404

import views_playbooks

from .models import ConfigurationTemplate, Category
from .models import Playbook

from .lib.spotmax import netspot
from .lib.spotmax import spotmax

def get_config(variables, template):
  """Generate config.

  Args:
    variables: dict, key = variable name
                     value = variable value
    template: ConfigurationTemplate object

  Returns:
    config_file, config, error: tuple, file path, config, error
  """

  # Generate configuration
  try:
    tpl = Template(template.template)
    config = tpl.render(Context(variables))
    error = False
  except TemplateSyntaxError as syntax_error:
    config = str(syntax_error)
    error = True

  # Check if temp directory exists
  if not os.path.exists(settings.TEMP_DIRECTORY):
    os.makedirs(settings.TEMP_DIRECTORY)

  # Write configuration to a file
  config_filename = str(uuid.uuid4())
  file_path = os.path.join(settings.TEMP_DIRECTORY, config_filename)
  with open(file_path, 'w') as config_file:
    config_file.write(config.encode('utf-8').strip())

  return file_path, config, error

@login_required
def index(request):
  """Index view."""

  # Dict to hold templates per category
  templates = defaultdict()

  # Get all categories
  categories = Category.objects.order_by('-name')

  # Get all templates per category
  for category in categories:
    # Get all templates
    templates[category] = ConfigurationTemplate.objects.filter(category=category).order_by('-name')

  return render(
      request,
      'templify/templates.htm',
      context={'templates': templates},
  )

@login_required
def download(request, filename):
  """File download."""

  file_path = os.path.join(settings.TEMP_DIRECTORY, filename)
  if os.path.exists(file_path):
    with open(file_path, 'rb') as filehandle:
      response = HttpResponse(filehandle.read(), content_type="application/text/plain")
      response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)
      return response

  raise Http404

@login_required
def generate_config(request):
  """Generate config view."""

  # Get template
  template_id = request.POST.get('template_id', None)
  asset_name = request.POST.get('asset_name', None)
  template = get_object_or_404(ConfigurationTemplate, pk=template_id)

  # Remove unnecessary POST data
  data = dict(request.POST)
  try:
    del data['csrfmiddlewaretoken']
    del data['template_id']
  except KeyError:
    pass

  # Variables to be used in template
  variables = defaultdict()

  # Get group variables if asset_name is available
  inventory = netspot.NetSPOT()

  if asset_name:
    asset_details = inventory.search(asset_name, key='asset')[0]

    # Get variable for each group
    for group in asset_details['groups']:
      group_details = spotmax.SPOTGroup().search(group, key='group')[0]

      # Get user variables if any
      if group_details['variables']:
        for variable in group_details['variables']:
          variables.update(variable)

  # Get variables from user input
  # Overwrite existing variables. User input is more specific.
  for variable in data:
    # If interface, split and strip each interface in the list
    if variable == 'interfaces':
      interfaces = data[variable][0].split(',')
      if len(interfaces) == 1:
        variables['interface'] = interfaces[0].strip()
        variables['interfaces'] = [interfaces[0].strip()]
      else:
        variables['interface'] = ''
        variables['interfaces'] = [x.strip() for x in interfaces]
    else:
      variables[variable] = data[variable][0]

  file_path, config, error = get_config(variables, template)

  # Get playbooks that accepts templates as input
  playbooks = Playbook.objects.filter(template_input=True)

  # If a playbook is specified go directly to playbook input
  if template.playbook:
    return views_playbooks.playbook_input(request,
                                          playbook_id=template.playbook.id,
                                          config_file=file_path,
                                          template=template.template)
  return render(
      request,
      'templify/config.htm',
      context={'config': config,
               'asset_name': asset_name,
               'config_filename': file_path,
               'template': template,
               'error': error,
               'playbooks': playbooks,
               'template_id': template_id},
  )

@login_required
def template_input(request, template_id):
  """Playbook input view."""

  # Get template
  template = get_object_or_404(ConfigurationTemplate, pk=template_id)

  # Check if port and asset is provided
  asset_name = request.POST.get('asset_name', None)
  interfaces = request.POST.getlist('interfaces', [])

  return render(
      request,
      'templify/template.htm',
      context={'template': template,
               'asset_name': asset_name,
               'interfaces_str': ', '.join(interfaces),
               'interfaces': interfaces},
  )
