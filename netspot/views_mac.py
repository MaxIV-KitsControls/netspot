"""NetSPOT MAC views."""

from collections import defaultdict

import helpers
import netspot_settings

from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from .lib.spotmax import netspot

# IP Usage
@login_required
def ipusage(request):
  """Lists all assets."""

  inventory = netspot.NetSPOT(collection=netspot_settings.COLL_IP)
  search_result = inventory.search('', key='ip', sort=[("date", 1), ("time", 1)], limit=20)

  return render(
      request,
      'ipusage.htm',
      context={'filter': '', 'ips': search_result,},
  )

@login_required
def ipusagesearch(request):
  """Search."""

  # Get search term
  find = helpers.get_search_term(request)

  # Search
  inventory = netspot.NetSPOT(collection=netspot_settings.COLL_IP)
  search_result = inventory.search(find, key='ip', sort=[("date", 1), ("time", 1)])

  return render(
      request,
      'ipusage.htm',
      context={'ips': search_result, 'ipusagefilter': find},
  )

# MACs
@login_required
def macs(request):
  """Lists all assets."""

  # Get the MongoDB collection
  collection = helpers.mongo_helper(netspot_settings.COLL_MACS)
  num_assets = collection.count()

  # Number of MACs
  try:
    num_macs = collection.aggregate([{"$unwind":"$macs"},
                                     {"$group": {"_id":"$macs"}},
                                     {"$group": {"_id":"DistictCount",
                                                 "count": {"$sum": 1}}}]).next()
    num_macs = num_macs['count']
  except StopIteration:
    num_macs = 0

  return render(
      request,
      'macs.htm',
      context={'filter': '', 'num_assets': num_assets, 'num_macs': num_macs},
  )

@login_required
def macsearch(request):
  """Search."""

  # Get search term
  find = helpers.get_search_term(request)

  # Get key and value from search
  key, value = netspot.NetSPOT().parse_variable(find)

  # Search
  inventory = netspot.NetSPOT(collection=netspot_settings.COLL_MACS)
  search_result = inventory.search(find, key='asset', sort='asset')

  # Filter out any other MAC entries
  counter = 0
  if key:
    search_filtered = []
    for asset in search_result:
      entry = defaultdict()
      entry['asset'] = asset['asset']
      if asset.get('macs'):
        for mac in asset['macs']:
          if mac[key] and value in mac[key]:
            entry['macs'] = [mac]
            search_filtered.append(entry)
            counter += 1
    search_result = search_filtered
  else:
    counter = len(search_result[0]['macs'])

  return render(
      request,
      'macs.htm',
      context={'devices': search_result,
               'result_counter': counter,
               'macfilter': find},
  )
