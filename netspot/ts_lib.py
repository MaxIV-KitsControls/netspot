#!/usr/bin/python -tt

"""Junos Interface Troubleshooting library."""

import re
import warnings
import helpers

from napalm import get_network_driver
from jnpr.junos.exception import ConnectRefusedError, ConnectAuthError

# JUNOS MAC table RE
RE_VLAN = r'\s+([\w\d-]+)\s+'
RE_MAC = r'\s?([*\w\d:]+)\s+'
RE_TYPE = r'\s?([\w]+) '
RE_AGE = r'\s+([-\d:]+)'
RE_INTERFACE = r'\s+([-.\w\d/]+)'
RE_SWITCHING_TABLE = RE_VLAN + RE_MAC + RE_TYPE + RE_AGE + RE_INTERFACE


class TroubleshootDevice(object):
  """Class to help troubleshoot device."""

  def __init__(self, asset, loopback, ssh_key, interface_name):
    self.asset = asset
    self.loopback = loopback
    self.ssh_key = ssh_key
    self.interface_name = interface_name
    self.mac_address = None
    self.dhcp_logs = None
    self.dhcp_error = None
    self.log_entries = None
    self.interface = None
    self.error_message = None
    self.macs = {}
    self.lldp = {}

  def run(self):
    """Run troubleshooter."""

    try:
      # Connect to asset
      driver = get_network_driver('junos')
      device = driver(self.loopback,
                      'automation',
                      '',
                      optional_args={'key_file': self.ssh_key})
      device.open()
      with warnings.catch_warnings(record=True) as warning:
        warnings.filterwarnings('ignore')

        # Check interface
        cmd = 'show interfaces {0} detail'.format(self.interface_name)
        show_interface = device.cli([cmd])
        self.interface = Interface(show_interface[cmd])

        if self.interface.link_state == 'Up':
          # Get LLDP neighbor
          cmd = 'show lldp neighbors interface {0}'.format(self.interface_name)
          lldp_neighbor = device.cli([cmd])
          self.lldp = LLDP(lldp_neighbor[cmd])

          # Check MAC table
          cmd = 'show ethernet-switching table interface {0}'.format(self.interface_name)
          mac_table = device.cli([cmd])
          self.macs = MACTable(mac_table[cmd])

          # Search DHCP logs if MAC is specified
          if self.macs:
            self.mac_address = self.macs.mac_entries[0]['mac']
            dhcp_server = helpers.get_dhcp_server(asset=self.asset)
            self.dhcp_logs, self.dhcp_error = helpers.search_dhcp_log(self.mac_address, dhcp_server)

        # Check log file
        cmd = 'show log messages'
        show_log = device.cli([cmd])
        show_log = show_log[cmd]
        self.log_entries = re.findall(r'\n([\[\]\s\w\d:.-]+{0}[\s\w\d:.-]+)\n'.format(self.interface_name),
                                      show_log)

        device.close()

    except ConnectAuthError:
      self.error_message = 'Autentication failed to %s.' % self.loopback
    except ConnectRefusedError:
      self.error_message = 'Connection refused to %s.' % self.loopback
    except ValueError:
      self.error_message = 'No switch found.'

class Interface(object):
  """Class to represent a JUNOS interface."""

  def __init__(self, output):
    self.output = output

    self.link_state = ''
    self.speed = ''
    self.duplex = ''
    self.flapped = ''
    self.auto_neg = ''

    # Analyze output
    self.analyze_output()

  def analyze_output(self):
    """Anlyze the output from show interfaces X."""

     # Link down
    match = re.search(r'Physical link is ([\w]+)', self.output)
    if match:
      self.link_state = match.groups()[0]

    # Speed
    match = re.search(r'Speed: ([\w\d]+),', self.output)
    if match:
      self.speed = match.groups()[0]

    # Duplex
    match = re.search(r'Duplex: ([\w-]+),', self.output)
    if match:
      self.duplex = match.groups()[0]

    # Last flapped
    match = re.search(r'Last flapped   : ([\w\d ():-]+)\n', self.output)
    if match:
      self.flapped = match.groups()[0]

    # Auto negotiation
    match = re.search(r'Auto-negotiation: ([\w]+),', self.output)
    if match:
      self.auto_neg = match.groups()[0]


class LLDP(object):
  """Parse and represent a LLDP neighbor."""

  def __init__(self, output):
    self.output = output
    self.empty = True

    self.remote_chassis_id = ''
    self.remote_port_description = ''
    self.remote_system = ''

    # Analyze output
    self.analyze_output()

    if self.remote_chassis_id:
      self.empty = False

  def analyze_output(self):
    """Parse JUNOS show lldp neighboir interface X command."""

    # Remote chassis ID
    match = re.search(r'Chassis ID\s+: ([\w\d:-]+)', self.output)
    if match:
      self.remote_chassis_id = match.groups()[0]

    # Remote port description
    match = re.search(r'Port description\s+: ([\w\d\/:-]+)', self.output)
    if match:
      self.remote_port_description = match.groups()[0]

    # Remote port system
    match = re.search(r'System name\s+: ([\w\d\/:-]+)', self.output)
    if match:
      self.remote_system = match.groups()[0]

class MACTable(object):
  """Parse and save MAC entries from a JUNOS device."""

  def __init__(self, output):
    self.output = output

    self.mac_entries = []

    # Analyze output
    self.analyze_output()

  def analyze_output(self):
    """Parse JUNOS show ethernet-switching interface X command."""

    # Remote chassis ID
    match = re.findall(RE_SWITCHING_TABLE, self.output)
    for entry in match:
      if entry[1] != '*':
        mac_entry = {'vlan': entry[0],
                     'mac': entry[1],
                     'type': entry[2],
                     'age': entry[3],
                     'interface': entry[4]}
        self.mac_entries.append(mac_entry)

  def __str__(self):
    if self.mac_entries:
      return self.mac_entries[0]['mac']
    return None

def main():
  """Main."""
  pass

if __name__ == '__main__':
  main()
