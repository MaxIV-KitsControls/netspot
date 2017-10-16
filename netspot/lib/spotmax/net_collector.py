#!/usr/bin/python -W ignore -tt

"""Module to collect data from network devices."""

from collections import defaultdict
from datetime import datetime
import sys
import re
import warnings
import ipaddress

import helpers
import netspot

from napalm import get_network_driver
from spotmax import SpotMAX

# JUNOS Ethernet swtich table RE
RE_VLAN = r'\s+([\w\d-]+)\s+'
RE_MAC = r'\s?([*\w\d:]+)\s+'
RE_TYPE = r'\s?([\w]+) '
RE_AGE = r'\s+([-\d:]+)'
RE_INTERFACE = r'\s+([-.\w\d/]+)'
RE_SWITCHING_TABLE = RE_VLAN + RE_MAC + RE_TYPE + RE_AGE + RE_INTERFACE

class NetCollector(object):
  """NetCollector class."""

  def __init__(self, hostname, username, password, ssh_keyfile=None):
    self.mac_arp_table = defaultdict()

    self.hostname = hostname

    # Check if hostname is IP address instead of hostname
    try:
      self.loopback_ip = str(ipaddress.ip_address(unicode(hostname)))

      # Hostname is given as IP address - need to find asset name
      inventory = netspot.NetSPOT()
      assets = inventory.search(hostname, key='loopback')
      for asset in assets:
        if hostname == asset['loopback']:
          self.hostname = asset['asset']
    except ValueError:
      # Resolve hostname
      try:
        self.loopback_ip = helpers.resolv(hostname)[0]
      except helpers.CouldNotResolv:
        self.loopback_ip = None
        sys.exit('Could not resolv hostname: %s' % hostname)


    self.device_macs = {'asset': self.hostname,
                        'macs': []}

    # Connect and get data from device
    driver = get_network_driver('junos')

    if ssh_keyfile:
      device = driver(self.loopback_ip, username, password, optional_args={'key_file': ssh_keyfile})
    else:
      device = driver(self.loopback_ip, username, password)
    device.open()

    # Get MAC and ARP tables
    self.macs = device.get_mac_address_table()
    self.arps = device.get_arp_table()

    # Due to a bug with the JUNOS API some devices returns 0 MACs
    if len(self.macs) == 0:
      self._get_mac_table(device)

    # Close device connection
    device.close()

    # Analyze collected data
    self.analyze_data()

  def analyze_data(self):
    """Run methods to generate a common MAC-ARP table."""
    self._extract_arp()
    self._extract_macs()

  def _extract_arp(self):
    """Extract ARPs and creates ARP entries."""

    for arp in self.arps:
      arp_entry = {'interface': arp['interface'],
                   'mac': arp['mac'],
                   'last_move': None,
                   'moves': None,
                   'vlan': None,
                   'static': None,
                   'ip': arp['ip']}

      self.mac_arp_table[arp['mac']] = arp_entry

  def _extract_macs(self):
    """Extract MAC addresses and create MAC entries."""
    for mac in self.macs:
      # Get IP
      if self.mac_arp_table.get(mac['mac']):
        ip_address = self.mac_arp_table[mac['mac']]['ip']
      else:
        ip_address = None

      # Create entry
      mac_entry = {'interface': mac['interface'],
                   'mac': mac['mac'],
                   'last_move': mac['last_move'],
                   'moves': mac['moves'],
                   'vlan': mac['vlan'],
                   'static': mac['static'],
                   'ip': ip_address}
      self.device_macs['macs'].append(mac_entry)

  def _get_mac_table(self, device):
    """Run CLI command to get ethernet switch table.

    Args:
      device: NAPALM device object
    """

    with warnings.catch_warnings(record=True) as warning:
      warnings.filterwarnings('ignore')
      macs = device.cli(['show ethernet-switching table'])

    mac_entry = re.findall(RE_SWITCHING_TABLE, macs.values()[0])
    mac_result = list()

    if mac_entry:
      for mac in mac_entry:
        # Ignore '*' MAC
        if mac[1] == '*':
          continue

        # Check if MAC is static
        static = False
        if mac[2] == 'Static':
          static = True

        mac_result.append({'interface': mac[4],
                           'mac': mac[1].upper(),
                           'vlan': mac[0],
                           'moves': None,
                           'last_move': None,
                           'static': static})

    self.macs = mac_result

class IPUsage(SpotMAX):
  """Class that save IP usage to database."""

  def __init__(self, device_macs, database=netspot.DATABASE, collection=netspot.COLL_IP):
    SpotMAX.__init__(self, database, collection)
    #super(IPUsage, self).__init__(database, collection)
    self.device_macs = device_macs

  def uppdate_ip(self):
    """Add or update IP address entry in database."""

    # Get time and date
    now = datetime.now()

    for mac in self.device_macs['macs']:
      if mac['ip']:
        ip_address = {'date': now.strftime("%Y-%m-%d"),
                      'time': now.strftime("%H:%M"),
                      'ip': mac['ip'],
                      'vlan': mac['vlan'],
                      'mac': mac['mac'],
                      'asset': self.device_macs['asset'],
                      'interface': mac['interface']
                     }

        if not self._exist(mac['ip'], key='ip'):
          # Add asset to database
          self.collection.insert_one(ip_address)
        else:
          update = {"$set": ip_address}

          self.collection.update_one({'ip': mac['ip']}, update)

if __name__ == '__main__':
  pass
