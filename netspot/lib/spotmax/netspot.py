#!/usr/bin/python -tt

"""NetSPOT - Network SPOT

Interact with the netspot database.

"""

from datetime import datetime
from spotmax import SpotMAX
from network_device import NetworkDevice

import netspot_settings

# Defaults
DATABASE = netspot_settings.DATABASE
COLL_NETSPOT = netspot_settings.COLL_NETSPOT
COLL_NETSPOT_GROUPS = netspot_settings.COLL_NETSPOT_GROUPS
COLL_MACS = netspot_settings.COLL_MACS
COLL_PLAYBOOK_LOGS = netspot_settings.COLL_PLAYBOOK_LOGS


class Asset(object):
  """Class to represent an asset."""

  def __init__(self,
               asset,
               loopback=None,
               groups='',
               username=None,
               password=None,
               ssh_keyfile=None):
    """Init.

    Args:
      asset: string, name of device
      loopback: string, IP address
      groups: string, comman separeted list of group names
      username: string, username to login to device
      password: string, password for the username
    """

    self.asset = asset
    self.loopback = loopback

    # Get all groups / convert to list
    if ',' in groups:
      self.groups = groups.split(',')
    else:
      self.groups = [groups]

    self.username = username
    self.password = password
    self.ssh_keyfile = ssh_keyfile


class NetSPOT(SpotMAX):
  """Class that interacts with the MongoDB backend."""

  def __init__(self, database=DATABASE, collection=COLL_NETSPOT):
    SpotMAX.__init__(self, database, collection)

  def _update_discover_data(self, asset, facts):
    """Update discoverd data for a given asset.

    Args:
      asset: string, name of the asset
      facts: dict, dict with with assets facts
    """

    device = self._extract_device(facts)

    update = {
        "$set": device,
        "$currentDate": {'lastModified': True}
    }

    cursor = self.collection.update_one({"asset": asset}, update)

    if cursor.matched_count == 1:
      print '%s updated sucessfully.' % asset
    else:
      print 'Failed to update database.'

  @staticmethod
  def _extract_device(facts):
    """Returns a list of devices extracted from JUNOS device.facts.

    Args:
      facts: jnpr.junos.Device.facts, dict of facts

    Returns:
      device: dict, device facts in a dict
    """

    # Construct new_device
    new_device = {'hostname': facts['hostname'],
                  'vendor': 'JUNIPER',
                  'fqdn': facts['fqdn'],
                  'uptime': facts['uptime'],
                  'model': facts['model'],
                  'serial': facts['serial_number'],
                  'version': facts['os_version']
                 }

    # Add additional information for dual RE devcies
    if facts.get('2RE'):
      # JUNOS supports up to 10 stack members
      for i in range(0, 10):
        re_i = 'RE%i' % i
        version = facts.get('version_%s' % re_i)
        routing_engine = facts.get(re_i)

        # JUNOS version
        if version:
          new_device['%s_version' % (re_i.lower())] = version

        # Model
        if routing_engine:
          model = facts.get(re_i).get('model')
          if model:
            if ',' in model:      # model = 'EX4200T, 8POE'
              model = model.split(',')[0]
            new_device['%s_model' % (re_i.lower())] = model

    return new_device

  def add_new_asset(self, asset):
    """Add new asset.

    Args:
      asset: Asset object

    Returns:
      Boolean: True, asset added
               False, asset not added
    """

    if self._exist(asset.asset, key='asset'):
      return False

    # Connect to device
    print 'Gathering device facts.'
    device = NetworkDevice(asset.loopback, asset.username, asset.password, asset.ssh_keyfile)

    # Create device to add to database
    new_device = self._extract_device(device.facts)
    new_device['asset'] = asset.asset
    new_device['loopback'] = asset.loopback
    new_device['groups'] = asset.groups

    # Add asset to database
    self.collection.insert_one(new_device)

    # Add all interfaces
    self.update_interfaces(asset.asset, device)
    return True

  def count_interfaces(self):
    """Return the total number of interfaces."""

    try:
      num_interfaces = self.collection.aggregate([{"$unwind":"$interfaces"},
                                                  {"$group": {"_id":"$interfaces"}},
                                                  {"$group": {"_id":"DistictCount",
                                                              "count": {"$sum": 1}}}]).next()
      num_interfaces = num_interfaces['count']
    except StopIteration:
      num_interfaces = 0

    return num_interfaces

  def discover(self, asset):
    """Discover asset data and updates database.

    Args:
      asset: Asset object

    Returns:
      Boolean: True, dicover successfull
               False, discover failed
    """

    # Find asset to update
    cursor = self.collection.find_one({'asset': asset.asset})

    if cursor:
      # Connect to device
      device = NetworkDevice(cursor['loopback'], asset.username, asset.password, asset.ssh_keyfile)

      # Update disocvered data
      self._update_discover_data(asset.asset, device.facts)
      self.update_interfaces(asset.asset, device)
      return True
    else:
      return False

  def update_interfaces(self, asset, device):
    """Update or add interfaces for a given asset.

    Args:
      asset: string, asset name
      device: NetworkDevice object
    """

    interfaces = list()

    for port in device.interfaces:
      # Filter physical interfaces
      if ('ge-' in port or
          'xe-' in port or
          'et-' in port or
          'me0' in port or
          'reth' in port or
          'ae' in port):

        # Check description. Bug in JUNOS reports "description" for empty descriptions
        if device.interfaces[port]['description'] == 'description':
          description = None
        else:
          description = device.interfaces[port]['description']

        # Port speed
        if device.interfaces[port]['speed'] != -1:
          speed = device.interfaces[port]['speed']
        else:
          speed = ''

        # Get VLAN id
        vlans = list()
        for vlan in device.vlans:
          if port in vlan['tagged_interfaces']:
            vlans.append(vlan['vlan'])
          if port in vlan['untagged_interfaces']:
            vlans.append(vlan['vlan'])

        try:
          vlans.sort(key=int)
        except ValueError:
          pass

        # Get LLDP neighbor(s)
        lldp_neighbors = list()
        neighbors = device.lldp.get(port, [])
        if not neighbors:
          neighbors = device.lldp.get(port + '.0', [])

        for lldp_neighbor in neighbors:
          lldp_neighbors.append(lldp_neighbor['hostname'] + ':' + lldp_neighbor['port'])

        # Create new interface
        new_interface = {
            'interface': port,
            'description': description,
            'mac': device.interfaces[port]['mac_address'].upper(),
            'speed': speed,
            'lldp_neighbor': lldp_neighbors,
            'vlan': ', '.join(vlans)
            }

        # Add interface to list
        interfaces.append(new_interface)

    # Update the asset with the new interface information
    cursor = self.collection.update_one({'asset': asset},
                                        {'$set': {'interfaces': interfaces}})

    return cursor

def main():
  """Do nothing."""
  pass

if __name__ == '__main__':
  main()
