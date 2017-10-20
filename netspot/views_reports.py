"""NetSPOT reports."""

from collections import defaultdict

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
import helpers
import netspot_settings

class Report(object):
  """Class to represent a report."""

  def __init__(self, name, description, headers, rows):
    self.name = name
    self.description = description
    self.headers = ['Model', 'Version(s)']

    self.data = {'headers':  headers,
                 'rows': sorted(rows)}

    # Context for webpage rendering
    self.context = {'result': self.data, 'name': self.name, 'description': self.description}


@login_required
def reports(request):
  """Reports index."""

  return render(
      request,
      'reports.htm',
      context={},
  )

@login_required
def report_model(request):
  """Reports: Model."""

  # DB Search
  collection = helpers.mongo_helper(netspot_settings.COLL_NETSPOT)
  models = collection.aggregate([{'$group' : {'_id': {'model': '$model',
                                                      're0_model': '$re0_model',
                                                      're1_model': '$re1_model'},
                                              'count':{'$sum':1}}}])

  # Prepare data. Return dict
  result = defaultdict()
  for model in models:
    for sub_model in model['_id']:
      if result.get(model['_id'][sub_model]):
        result[model['_id'][sub_model]] += model['count']
      else:
        result[model['_id'][sub_model]] = model['count']

  rows = list()
  for model in result:
    rows.append([model, result[model]])

  # Create report
  report = Report(name='Models',
                  description='Number of different asset models.',
                  headers=['Model', 'Count'],
                  rows=rows)

  return render(
      request,
      'report.htm',
      context=report.context
  )

@login_required
def report_junos_version(request):
  """Report: JUNOS versions."""

  # DB Search
  collection = helpers.mongo_helper(netspot_settings.COLL_NETSPOT)
  models = collection.aggregate([{'$group':  {'_id': {'model':'$model', 'version': '$version'},
                                              'count': {'$sum': 1}}}])

  rows = list()
  for model in models:
    rows.append([model['_id']['model'], model['_id']['version']])

  # Create report
  report = Report(name='JUNOS Versions',
                  description='Number of different JUNOS versions.',
                  headers=['Model', 'Version(s)'],
                  rows=rows)

  return render(
      request,
      'report.htm',
      context=report.context
  )

@login_required
def report_playbook_runs(request):
  """Report: Playbooks runs."""

  # DB Search
  collection = helpers.mongo_helper(netspot_settings.COLL_PLAYBOOK_LOGS)
  playbooks = collection.aggregate([{'$group':  {'_id': {'playbook':'$playbook'},
                                                 'count': {'$sum': 1}}}])

  rows = list()
  for playbook in playbooks:
    rows.append([playbook['_id']['playbook'], playbook['count']])

  # Create report
  report = Report(name='Playbook runs',
                  description='Number of times a given playbook have been run.',
                  headers=['Playbook', 'Number of runs'],
                  rows=rows)

  return render(
      request,
      'report.htm',
      context=report.context
  )
