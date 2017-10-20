# -*- coding: utf-8 -*-

"""Views."""

from __future__ import unicode_literals

import operator
import nm_helper
import cdb_helper
import netspot_settings

from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from .lib.spotmax import netspot


@login_required
def netmagis(request):
  """NetMagis landing page."""

  return render(
      request,
      'netmagis/netmagis.htm',
      context={},
  )

@login_required
def networks(request):
  """NetMagis networks."""

  # Get all networks
  with nm_helper.NetMagisDB() as nmdb:
    nm_networks = nmdb.query("SELECT * from dns.network")

  return render(
      request,
      'netmagis/networks.htm',
      context={'networks': nm_networks},
  )

@login_required
def searchhost(request):
  """NetMagis networks."""

  # Get search parameter
  search = request.POST.get('search', None)

  # Return NetMagis entries
  netmagis_result = list()

  # Search in NetMagis
  with nm_helper.NetMagisDB() as nmdb:
    hosts = nmdb.search(search)

    for host in hosts:
      # Create host entry. Assume CNAME-record if MAC and ADDR is missing
      if host['mac'] or host['addr']:
        netmagis_result.append({'idrr': host['idrr'],
                                'name': host['name'],
                                'addr': host['addr'],
                                'mac': host['mac'],
                                'date': host['date'],
                                'comment': host['comment']})
      else:
        # Add CNAME record
        netmagis_result.append({'idrr': host['idrr'],
                                'name': '',
                                'addr': 'CNAME',
                                'mac': host['name'],
                                'date': host['date'],
                                'comment': host['comment']})

        # Find A-records for any CNAME-records in hosts
        if not host['addr']:
          # Get A record
          arecord = nmdb.get_arecord(host['idrr'])
          if arecord:
            host_entry = {'idrr': arecord[0]['idrr'],
                          'name': arecord[0]['name'],
                          'addr': arecord[0]['addr'],
                          'mac': arecord[0]['mac'],
                          'date': arecord[0]['date'],
                          'comment': arecord[0]['comment']}

            # Add if this arecord is not in netmagis_result already
            if host_entry not in netmagis_result:
              netmagis_result.append(host_entry)

  # Search for MACs
  inventory = netspot.NetSPOT(collection=netspot_settings.COLL_MACS)
  mac_search = []

  # Find MAC addresses in the MAC database
  for host in netmagis_result:
    # If missing - skip
    if not host['mac']:
      continue

    # Find interface in the MAC database
    search_result = inventory.search('mac:%s' % host['mac'].upper(), key='asset', sort='asset')

    # Filter out any other MAC entries
    for asset in search_result:
      for mac in asset.get('macs', []):
        if host['mac'].upper() in mac.get('mac', ''):
          mac_search.append({'asset': asset['asset'],
                             'mac': mac['mac'],
                             'ip': mac['ip'],
                             'interface': mac['interface'],
                             'vlan': mac['vlan']})

  # Find outlet for each physical interface
  for entry in mac_search:
    if 'xe-' in entry['interface'] or 'ge-' in entry['interface']:
      entry['outlet'] = cdb_helper.get_network_outlet(entry['asset'], entry['interface'])

  return render(
      request,
      'netmagis/searchhost.htm',
      context={'hosts': sorted(netmagis_result, key=operator.itemgetter('name'), reverse=True),
               'mac_search': mac_search,
               'search': search},
  )
