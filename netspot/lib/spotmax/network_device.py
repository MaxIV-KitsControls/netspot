#!/usr/bin/python -tt

"""Module to connect and discover JUNOS devices."""

# pylint: disable=E0611

import sys
import re
import warnings

from jnpr.junos.op.phyport import PhyPortTable
from jnpr.junos.exception import ConnectRefusedError, ConnectAuthError
from napalm import get_network_driver

class NetworkDevice(object):
  """Class that connects and discovers JUNOS devices."""

  def __init__(self, ip_address, username=None, password=None, ssh_keyfile=None):
    self.ip_address = ip_address
    self.facts = None
    self.ports = None
    self.username = username
    self.password = password
    self.vlans = list()

    # Connect and get data from device
    driver = get_network_driver('junos')

    if ssh_keyfile:
      self.device = driver(self.ip_address,
                           self.username,
                           self.password,
                           optional_args={'key_file': ssh_keyfile})
    else:
      self.device = driver(self.ip_address, self.username, self.password)

    try:
      self.device.open()

      # Get facts and interfaces
      self.facts = self.device.get_facts()
      self.interfaces = self.device.get_interfaces()

      # Get VLAN information
      with warnings.catch_warnings(record=True) as warning:
        warnings.filterwarnings('ignore')
        vlan_cli_output = self.device.cli(['show vlans detail'])
      if 'qfx' in self.facts['model'].lower():
        self.get_vlan_information_qfx(vlan_cli_output['show vlans detail'])
      else:
        self.get_vlan_information(vlan_cli_output['show vlans detail'])

      # LLDP neighbors
      self.lldp = self.device.get_lldp_neighbors()

    except ConnectAuthError:
      print 'Autentication failed to %s.' % self.ip_address
      sys.exit(1)
    except ConnectRefusedError:
      print 'Connection refused to %s.' % self.ip_address
      sys.exit(1)
    finally:
      # Close device connection
      self.device.close()

  def get_vlan_information_qfx(self, output):
    """Retrieve VLAN information from 'show vlan detail' from a QFX swtich.

    Args:
      output: string, output from 'show vlan detail'
    """

    for entry in output.split('Total MAC count'):
      tagged = []
      re_tagged_interfaces = re.findall(r'([\w\d\/*.-]+),tagged,', entry)
      for interface in re_tagged_interfaces:
        tagged.append(self.clean_interface(interface))

      untagged = []
      re_untagged_interfaces = re.findall(r'([\w\d\/*.-]+),untagged,', entry)
      for interface in re_untagged_interfaces:
        untagged.append(self.clean_interface(interface))

      vlan_name = re.search(r'VLAN Name: ([\w\d-]+)\s', entry)
      vlan_id = re.search(r'Tag: ([\d]+)\s', entry)

      try:
        vlan_data = {'vlan': vlan_id.groups(0)[0],
                     'name': vlan_name.groups(0)[0],
                     'untagged_interfaces': untagged,
                     'tagged_interfaces': tagged}
        self.vlans.append(vlan_data)
      except AttributeError:
        continue

  def get_vlan_information(self, output):
    """Retrieve VLAN information from 'show vlan detail' from a JUNOS swtich.

    Args:
      output: string, output from 'show vlan detail'
    """

    for entry in output.split('VLAN:'):
      vlan_name = re.search(r'([\w\d-]+), 802', entry)
      vlan_id = re.search(r'Tag: ([\d\w]+),', entry)

      # Get VLAN interfaces
      untagged, tagged = self.get_interfaces_per_vlan(entry)

      try:
        vlan_data = {'vlan': vlan_id.groups(0)[0],
                     'name': vlan_name.groups(0)[0],
                     'untagged_interfaces': untagged,
                     'tagged_interfaces': tagged}
        self.vlans.append(vlan_data)
      except AttributeError:
        continue

  def clean_interface(self, interface):
    """Clean interface name.

    Args:
      interface: string, interface name

    Returns:
      Cleaned up string
    """

    return interface.replace('*', '').replace('\n', '').replace(',', '').replace('.0', '')

  def get_interfaces_per_vlan(self, vlan_data):
    """Returns interfaces in vlan_data.

    Args:
      vlan_data: string, interface part from 'show vlan detail'

    Returns:
      tuple, (untagged, tagged) interfaces
    """

    untagged_interfaces = list()
    tagged_interfaces = list()

    untagged = re.findall(r'Untagged interfaces: ([\w\s*.,\/-]+)\n', vlan_data)
    if untagged:
      # Clean, split and remove empty entries
      untagged = self.clean_interface(untagged[0])
      untagged = untagged.split(' ')
      untagged_interfaces = filter(None, untagged)

    tagged = re.findall(r'Tagged interfaces: ([\w\s*.,\/-]+)\n', vlan_data)
    if tagged:
      # Clean, split and remove empty entries
      tagged = self.clean_interface(tagged[0])
      tagged = tagged.split(' ')
      tagged_interfaces = filter(None, tagged)

    return untagged_interfaces, tagged_interfaces

def main():
  """Do nothing."""
  pass

if __name__ == '__main__':
  main()
