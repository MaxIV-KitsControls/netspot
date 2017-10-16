"""NetSPOT Beamline user views."""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from .models import ConfigurationTemplate, Category


# Port provisioning
def pp_input(request):
  """Port provisioning."""

  # Get templates
  try:
    category = Category.objects.get(name='Network ports')
    port_templates = ConfigurationTemplate.objects.filter(category=category).order_by('-name')
  except ObjectDoesNotExist:
    port_templates = []

  return render(
      request,
      'pa/port.htm',
      context={'base': 'beamlines/base.htm',
               'port_templates': port_templates},
  )
