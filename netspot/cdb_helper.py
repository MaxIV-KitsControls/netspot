#!/usr/bin/python -tt

"""Cable DB connection."""

import re
import MySQLdb
import helpers

from lib.spotmax import netspot


NETWORK = {'NETWORK-01': 'g',
           'NETWORK-02': 'b',
           'NETWORK-03': 'w',
           'g': 'NETWORK-01',
           'b': 'NETWORK-02',
           'w': 'NETWORK-03'}

BEAMLINE_CODE = {'B303A': 'nanomax',
                 'BSP02': 'femtomax',
                 'B311A': 'biomax',
                 'B316A': 'veritas',
                 'B317A': 'hippie',
                 'B308A': 'balder',
                 'B112A': 'finest',
                 'B110A': 'arpes',
                 'B111A': 'maxpeem',
                 'B107A': 'flexpes',
                 'B310A': 'cosaxs',
                 'B108A': 'species'}

class NoAssetFound(Exception):
  """No asset found."""
  pass

class CablePathEmpty(Exception):
  """Empty cable path returned."""
  pass

def main():
  """Main."""
  pass

def get_interface_beamline(cable_path):
  """Returns interface and beamline.

  Args:
    cable_path: list, cable path

  Returns
    tuple: interface and beamline
  """

  interface = None
  beamline = ''

  # Check cable length
  if len(cable_path) == 1:
    raise CablePathEmpty

  # Check if ASW is in the cable path
  if 'ASW' not in cable_path[-1][1] and 'ASW' not in cable_path[0][1]:
    raise NoAssetFound

  # Get beamline
  beamline = BEAMLINE_CODE.get(cable_path[-1][1].split('-')[0], '')

  # Get interface
  interface = get_interface(cable_path)

  # Get asset
  inventory = netspot.NetSPOT()
  asset_details = inventory.search(get_search_term(cable_path), key='asset')

  if not asset_details.count():
    raise NoAssetFound

  asset = asset_details[0]['asset']

  return asset + ':' + interface, beamline

def get_interface(cable_path):
  """Retrieve JUNOS interface from a given cable path.

  Args:
    cable_path: list, cable path

  Returns:
    interface: string, eg. 'ge-2/0/16'
  """

  # Find ASW, either first or last in the cable path
  if 'ASW' in cable_path[-1][1]:
    index = -1
  else:
    index = 0

  fpc = int(re.search(r'ASW-0(\d)', cable_path[index][1]).group(1))-1
  port = int(re.search(r'ETH_OUT(\d+)', cable_path[index][2].upper()).group(1))

  interface = 'ge-%s/0/%s' % (fpc, port)

  return interface

def get_search_term(cable_path):
  """Get search term.

  Args:
    cable_path: list, cable path

  Returns:
    search_term: string, eg w-a900911
  """

  # Find ASW, either first or last in the cable path
  if 'ASW' in cable_path[0][1]:
    index = 2
  else:
    index = -1

  # Get network (white, green or blue)
  network = cable_path[index][-1]

  location = re.match(r'[\w\d]+-([\w\d]+)-', cable_path[index][1])
  search = '%s-%s' %(NETWORK[network], location.group(1))

  return search.lower()

def get_outlet_from_cable_id(cable_id):
  """Return outlet from cable ID.

  Args:
    cable_id: string, cable ID eg 12674

  Return:
    outlet: string, outlet eg. B303A-A100383-NET-NO-08

  """

  sql_cable_id = """SELECT termination_name, code, channel_id, equipment_id
                    FROM cable_plugs_view WHERE cable_id='{0}'
                    ORDER BY termination_name+0;""".format(cable_id)
  result = query(sql_cable_id)

  for endpoint in result:
    if '-NET-PP-' in endpoint[1]:
      outlet = endpoint[1] + '-' + endpoint[2]
      break
    elif not 'PP' in endpoint[1]:
      outlet = endpoint[1].replace('-NET-', '-') + '_' + endpoint[2].replace('ETH_', '')
      break

  return outlet

def get_outlet_port_code(outlet):
  """Returns outlet port and code.

  Args:
    outlet: string, outlet ID

  Returns:
    port, code: tuple, port and code
  """

  # Extract port and outlet code

  outlet = outlet.lower()

  outlet_port = ''
  outlet_code = ''

  match = re.search(r'([-\w\d]+)-(eth_[outin]+[\d]+)$', outlet)
  if match:
    outlet_code = match.groups()[0]
    outlet_port = match.groups()[1]
  else:
    match = re.search(r'([-\w\d]+)(_[outin]+[\d]+)$', outlet)
    if match:
      outlet_code = match.groups()[0]
      outlet_port = 'eth' + match.groups()[1].upper()

  outlet_code = outlet_code.upper()

  # Make sure NET is in outlet_code
  if 'NET' not in outlet_code:
    outlet_code = outlet_code.replace('-NO-', '-NET-NO-')
    outlet_code = outlet_code.replace('-ASW-', '-NET-ASW-')
    outlet_code = outlet_code.replace('-PP-', '-NET-PP-')

  return outlet_port, outlet_code


def get_network_outlet(hostname, interface):
  """Find outlet.

  Args:
    hostname: string, hostname
    interface: string, eg ge-7/0/13

  Returns:
    outlet: string, eg S-E120072-NET-NO-01_IN02
  """

  port = re.findall(r'\w\w-\d/\d/([\d]+)', interface)[0]
  fpc = re.findall(r'\w\w-([\d]+)/\d/\d', interface)[0]
  location = re.findall(r'\w-([\w\d.]+)-', hostname)[0]
  network_code = NETWORK[hostname[:1]]
  outlet_search = '{0}-ETH_OUT{1}'.format(location.upper(), port)

  # Construct ASW
  asw = str(int(fpc) + 1)

  # Get port and code
  port, code = get_outlet_port_code(outlet_search)

  # Get cable ID
  query_string = """SELECT cable_id FROM cable_plugs_view
                    WHERE code LIKE '%{0}%'
                    AND code LIKE '%ASW-0{3}%'
                    AND configuration_code = '{2}'
                    AND channel_id='{1}';""".format(code, port, network_code, asw)
  output = query(query_string)

  if output:
    # Get cable path
    cable_path = get_cable_path(str(output[0][0]))

    # Check for -NO-
    if '-NO-' in cable_path[0][1]:
      index = 0
    else:
      index = -1

    # Return outlet plus port
    return cable_path[index][1] + cable_path[index][2].upper().replace('ETH', '')

def get_cable_path(outlet):
  """Wrapper function to get cable path.

  Args:
    outlet: string, outlet ID

  Returns:
    list of list, cable path
  """

  # Outlet needs to be '-ETH_' and not '_ETH_'
  if '_ETH_' in outlet.upper():
    outlet = outlet.replace('_ETH_', '-ETH_')

  # Is this a cable ID?
  match = re.search(r'^[a-zA-Z]?(\d+)$', outlet)
  if match:
    outlet = get_outlet_from_cable_id(match.groups()[0])

  # Port and outlet code
  port, code = get_outlet_port_code(outlet)

  cable_path = []
  cable_path.append(['Equipment & Channel:', code, port])
  get_cable_connected_to_equipment_channel(code,
                                           port,
                                           cable_path,
                                           False,
                                           False)

  # If there's no ASW in path. Lets try search the opposite direction of the path.
  if 'ASW' not in cable_path[0][1] and 'ASW' not in cable_path[-1][1]:
    if 'out' in port:
      port = port.lower().replace('out', 'in')
    else:
      port = port.lower().replace('in', 'out')

    cable_path = []
    cable_path.append(['Equipment & Channel:', code, port])
    get_cable_connected_to_equipment_channel(code,
                                             port,
                                             cable_path,
                                             False,
                                             False)

  return cable_path

def query(query_string):
  """Run database query."""

  db_host = "w-v-cabledb-0"
  db_user = "root"
  db_pass = "maxlab"
  db_name = "cabledb_test2"

  try:
    with MySQLdb.connect(db_host, db_user, db_pass, db_name) as db_session:
      db_session.execute(query_string)
    return db_session.fetchall()
  except MySQLdb.Error, error:
    print "Error %d: %s" % (error.args[0], error.args[1])
    return False

def does_equipment_channel_exist(code, channel_id, debug):
  """Check if equipment channel exist."""

  if debug:
    print '\n** does_equipment_channel_exist'

  code_exists = False
  channel_id_exists = False

  query_string = ("SELECT count(*) FROM cable_plugs_view "
                  "WHERE code='%s' AND channel_id='%s';" % (code, channel_id))
  output = query(query_string)

  if debug:
    print '  ', query_string
    print '  ', output

  if not output:
    return code_exists, channel_id_exists

  count_channel = output[0][0]

  if count_channel > 0:
    channel_id_exists = True
    code_exists = True

  if debug:
    print '   Equipment', code, 'exists?:       ', code_exists
    print '   Channel', channel_id, 'exists?:   ', channel_id_exists

  return code_exists, channel_id_exists

def get_buddy_channel(code, channel_id, map_of_cables, lc_port, debug):
  """Get buddy channel."""

  if debug:
    print '\n** get_buddy_channel'
    print '   input channel_id: ', channel_id

  # Simple switching of IN & OUT:
  if 'OUT' not in channel_id and 'IN' not in channel_id:
    return False
  if 'OUT' in channel_id:
    check_channel_id = channel_id.replace('OUT', 'IN')
  if 'IN'  in channel_id:
    check_channel_id = channel_id.replace('IN', 'OUT')

  # Trickier stuff:
  if channel_id.startswith('LC_'):
    check_channel_id = check_channel_id.replace('LC_', 'MPO_')
    check_channel_id = check_channel_id.split('_P')[0]
  if channel_id.startswith('MPO_') and lc_port:
    check_channel_id = check_channel_id.replace('MPO_', 'LC_')
    check_channel_id = check_channel_id + '_P' + lc_port

  if debug:
    print '   checking for:     ', check_channel_id

  query_string = ("SELECT channel_id FROM cable_plugs_view "
                  "WHERE code='%s' AND channel_id='%s';" % (code, check_channel_id))
  output = query(query_string)

  if debug:
    print '  ', query_string
    print '  ', output

  if not output:
    return False

  buddy_channel_id = output[0][0]
  map_of_cables.append(['Equipment & Channel:', code, buddy_channel_id])

  if debug:
    print '   On equipment', code, 'channel', channel_id, 'is connected to', buddy_channel_id

  return buddy_channel_id

def get_channel_at_other_end_of_cable(cable_id, code, channel_id, map_of_cables, lc_port, debug):
  """Get channel at the other end of the cable."""

  if debug:
    print '\n** get_channel_at_other_end_of_cable'

  query_string = ("SELECT code, channel_id, configuration_code FROM cable_plugs_view "
                  "WHERE cable_id='%s' "
                  "AND not (code='%s' "
                  "AND channel_id='%s');" % (cable_id, code, channel_id))
  output = query(query_string)

  if not output:
    return False, False

  other_code = output[0][0]
  other_channel_id = output[0][1]
  network = output[0][2]
  map_of_cables.append(['Equipment & Channel:', other_code, other_channel_id, network])

  if debug:
    print '   At the other end of cable', cable_id, 'is equipment:', other_code, 'channel:', other_channel_id

  # Check if this an 'LC_' channel, if so, save the port number:
  if other_channel_id.startswith('LC_'):
    lc_port = other_channel_id.split('_P')[1]
    if debug:
      print '   LC port found:', lc_port

  # Get the channel on the other side of the equipment connected to this channel:
  buddy_channel = get_buddy_channel(other_code, other_channel_id, map_of_cables, lc_port, debug)

  # Get the cable connected to this buddy channel
  if not buddy_channel:
    return False, False
  get_cable_connected_to_equipment_channel(other_code, buddy_channel, map_of_cables, lc_port, debug)

  return other_code, other_channel_id

def get_cable_connected_to_equipment_channel(code, channel_id, map_of_cables, lc_port, debug):
  """Get cable connected to channel."""

  if debug:
    print '\n** get_cable_connected_to_equipment_channel'

  # Search for a cable connected to the given equipment and channel:
  query_string = """SELECT cable_id FROM cable_plugs_view
                    WHERE code LIKE '%{0}%'
                    AND channel_id='{1}';""".format(code, channel_id)
  output = query(query_string)

  if debug:
    print '  ', query_string
    print '  ', output

  if not output:
    return False

  cable_id = output[0][0]
  map_of_cables.append(['Cable:', cable_id])

  if debug:
    print '   On equipment', code, 'channel', channel_id, 'cable', cable_id, 'is connected'

  # Check if this an 'LC_' channel, if so, save the port number:
  if channel_id.startswith('LC_'):
    lc_port = channel_id.split('_P')[1]
    if debug:
      print '   LC port found:', lc_port

  # Get the channel connected to the other end of the cable:
  remote_equipment, remote_channel = get_channel_at_other_end_of_cable(cable_id, code, channel_id, map_of_cables, lc_port, debug)

  return cable_id

def get_equipment_list(code):
  """Get equipment list."""

  header1 = ['Equipment']
  header2 = ['code']
  equipment_list = []
  equipment_list.append(header1)
  equipment_list.append(header2)

  query_string = ("SELECT distinct(ecv.code) FROM equipment_code_view AS ecv "
                  "JOIN Eq_Channel AS ech ON (ecv.equipment_id = ech.equipment_id) "
                  "WHERE ecv.code LIKE '%"+str(code)+"%' "
                  "AND (ech.description LIKE '%Ethernet%' OR ech.channel_id LIKE '%ETH%' "
                  "OR ech.channel_id LIKE '%SFPP%' OR ech.channel_id LIKE 'MPO_%' OR "
                  "ech.channel_id LIKE 'SC_%' OR ech.channel_id LIKE '%APC%' OR "
                  "ech.channel_id LIKE 'SFP%' OR ech.channel_id LIKE 'LC_%');")
  output = query(query_string)

  if not output:
    return False
  for row in output:
    equipment_list.append(row)

  return equipment_list

def get_table_for_equipment_channel(code):
  """Get table for rquipment channel."""

  header1 = ['Equipment ID', 'Channel', 'Description']
  header2 = ['code', 'channel_id', 'description']
  equipment_list = []
  equipment_list.append(header1)
  equipment_list.append(header2)

  query_string = ("SELECT ecv.code, ech.channel_id, ech.description FROM equipment_code_view AS ecv "
                  "JOIN Eq_Channel AS ech ON "
                  "(ecv.equipment_id = ech.equipment_id) WHERE ecv.code LIKE '%"+str(code)+"%' "
                  "and (ech.description LIKE '%Ethernet%' OR ech.channel_id LIKE '%ETH%' "
                  "OR ech.channel_id LIKE '%SFPP%' OR "
                  "ech.channel_id LIKE 'MPO_%' OR ech.channel_id LIKE 'SC_%' OR "
                  "ech.channel_id LIKE '%APC%' OR ech.channel_id LIKE 'SFP%' OR "
                  "ech.channel_id LIKE 'LC_%');")

  output = query(query_string)

  if not output:
    return False

  for row in output:
    equipment_list.append(row)

  return equipment_list

if __name__ == '__main__':
  main()
