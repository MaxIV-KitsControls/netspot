#!/usr/bin/python -tt

"""NetSPOT REST API."""

from rest_framework.decorators import api_view
from rest_framework.response import Response
import helpers
import nm_helper

from .lib.spotmax import netspot

# API
@api_view(['GET'])
def api_get_mac(request, ip_address):
  """Returns a list with MAC addresses for a given IP address.

  Args:
    ip_address: string, IP address
  """

  if request.method == 'GET':
    collection = helpers.mongo_helper(netspot.COLL_MACS)
    macs = collection.find({'macs.ip': {'$regex': ip_address}}).sort('asset')

    # Serialize response
    macs_response = set()
    for entry in macs:
      for mac in entry['macs']:
        if ip_address == mac['ip']:
          macs_response.add(mac['mac'])

    return Response(macs_response)

@api_view(['GET'])
def api_netmagis_search(request, search_keyword):
  """Search NetMagis.

  Args:
    search_keyword: string, IP address, hostname or MAC

  Returns:
    search_result: list of dict, search result
  """

  search_result = []

  if request.method == 'GET':
    with nm_helper.NetMagisDB() as nmdb:
      hosts = nmdb.search(search_keyword)

      for host in hosts:
        # Find A-records for any CNAME-records in hosts
        if not host['addr']:
          # Get A record
          arecord = nmdb.get_arecord(host['idrr'])
        else:
          arecord = None
        if arecord:
          record = arecord[0]
        else:
          record = host

        # Create entry
        entry = {'hostname': record['name'],
                 'ip_address': record['addr'],
                 'mac': record['mac']}

        # Append to result
        search_result.append(entry)

    return Response(search_result)

def main():
  """Main."""
  pass

if __name__ == '__main__':
  main()
