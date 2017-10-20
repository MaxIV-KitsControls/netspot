#!/usr/bin/python -tt
"""JUNOS link down test

  Run: python -m unittest tests.test_netspot

"""

import unittest
import netspot

from collections import namedtuple

from tests.test_spotmax import MockCollection

DEVICE1_FACTS = {'2RE': False,
                 'HOME': '/var/root',
                 'RE0': {'last_reboot_reason': '0x1:power cycle/failure ',
                         'mastership_state': 'master',
                         'model': 'EX4200-48T, 8 POE',
                         'status': 'OK',
                         'up_time': '84 days, 1 hour, 39 minutes, 25 seconds'},
                 'domain': None,
                 'fqdn': 'w-netlab-sw-4',
                 'hostname': 'w-netlab-sw-4',
                 'ifd_style': 'SWITCH',
                 'master': 'RE0',
                 'model': 'EX4200-48T',
                 'personality': 'SWITCH',
                 'uptime': '767686',
                 'serial_number': 'BP0212513097',
                 'switch_style': 'VLAN',
                 'vc_capable': True,
                 'vc_mode': 'Enabled',
                 'os_version': '14.1X53-D40.8',
                 'version_RE0': '14.1X53-D40.8',
                 'version_info': 'junos.version_info(major=(14, 1), type=X, minor=(53, "D", 40), build=8)'}

DEVICE2_FACTS = {'2RE': True,
                 'RE0': {'status': 'OK',
                         'last_reboot_reason':
                         '0x1:power cycle/failure ',
                         'model': 'EX4200-48T, 8 POE',
                         'up_time': '85 days, 5 hours, 14 minutes, 22 seconds',
                         'mastership_state': 'master'},
                 'RE1': {'status': 'OK',
                         'last_reboot_reason':
                         '0x1:power cycle/failure ',
                         'model': 'EX4200-48PX,48 POE+',
                         'up_time': '85 days, 5 hours, 14 minutes, 19 seconds',
                         'mastership_state': 'backup'},
                 'ifd_style': 'SWITCH',
                 'version_RE0': '12.2R4.5',
                 'version_RE1': '12.2R4.6',
                 'uptime': '767686',
                 'domain': 'net.maxiv.lu.se',
                 'serial_number': 'BP0212512984',
                 'fqdn': 'w-b080001-a-0.net.maxiv.lu.se',
                 'version_info': 'junos.version_info(major=(12, 2), type=R, minor=4, build=5)',
                 'switch_style': 'VLAN',
                 'os_version': '12.2R4.5',
                 'master': 'RE0',
                 'hostname': 'w-b080001-a-0',
                 'HOME': '/var/home/netAdmin',
                 'vc_mode': 'Enabled',
                 'model': 'Virtual Chassis',
                 'vc_capable': True,
                 'personality': 'SWITCH'}

# 4 device stack, RE0 and RE2 master/backup
DEVICE3_FACTS = {'2RE': True,
                 'domain': 'net.maxiv.lu.se',
                 'hostname': 'w-a111110-a-6',
                 'version_RE3': '13.2X51-D36.3',
                 'version_RE2': '13.2X51-D36.2',
                 'version_RE1': '13.2X51-D36.1',
                 'version_RE0': '13.2X51-D36.0',
                 'uptime': '767686',
                 'RE0': {'status': 'OK',
                         'last_reboot_reason': '0x1:power cycle/failure ',
                         'model': 'EX4300-48T',
                         'up_time': '22 days, 4 hours, 8 minutes, 12 seconds',
                         'mastership_state': 'master'},
                 'RE2': {'status': 'OK',
                         'last_reboot_reason':
                         '0x1:power cycle/failure ',
                         'model': 'EX4300-48P',
                         'up_time': '22 days, 4 hours, 8 minutes, 14 seconds',
                         'mastership_state': 'backup'},
                 'serial_number': 'PD3715050008',
                 'fqdn': 'w-a111110-a-6.net.maxiv.lu.se',
                 'version_info': 'junos.version_info(major=(13, 2), type=X, minor=(51, "D", 36), build=1)',
                 'switch_style': 'VLAN', 
                 'os_version': '13.2X51-D36.1',
                 'master': 'RE0',
                 'HOME': '/var/home/netAdmin',
                 'ifd_style': 'SWITCH',
                 'vc_mode': 'Enabled',
                 'model': 'Virtual Chassis',
                 'vc_capable': True,
                 'personality': 'SWITCH'}

# Named tuple for interfaces
Interface = namedtuple('Interface', ['name',
                                     'description',
                                     'macaddr',
                                     'mtu'])

class MockNetworkDevice(object):
  def __init__(self, asset, loopback=None, groups='', username=None, password=None, ssh_keyfile=None):

    if loopback == '1':
      self.facts = DEVICE1_FACTS
    else:
      self.facts = DEVICE2_FACTS

    self.interfaces = {'ge-0/0/6': {u'description': u'',
                                u'is_enabled': True,
                                u'is_up': False,
                                u'last_flapped': -1.0,
                                u'mac_address': u'54:E0:32:30:87:09',
                                u'speed': -1}}

    self.macs = [{u'active': True,
                  u'interface': u'ge-0/0/0.0',
                  u'last_move': 0.0,
                  u'mac': u'B8:27:EB:04:FF:A2',
                  u'moves': 0,
                  u'static': False,
                  u'vlan': 201},
                 {u'active': True,
                  u'interface': u'xe-0/1/0.0',
                  u'last_move': 0.0,
                  u'mac': u'F8:C0:01:38:4F:38',
                  u'moves': 0,
                  u'static': False,
                  u'vlan': 201},
                 {u'active': True,
                  u'interface': u'Router',
                  u'last_move': 0.0,
                  u'mac': u'54:E0:32:30:87:01',
                  u'moves': 0,
                  u'static': True,
                  u'vlan': 0}]

    self.vlans = list()
    self.lldp = dict()

class TestNetSPOT(unittest.TestCase):

  def setUp(self):
    netspot.NetworkDevice = MockNetworkDevice

    # Setup mock SpotMAX and collection
    self.ns = netspot.NetSPOT(database=None, collection=None)
    self.ns.collection = MockCollection()

    self.asset = netspot.Asset('w-netlab-sw-4',
                               loopback=None,
                               groups='test_group',
                               username='test_user',
                               password='test_password',
                               ssh_keyfile=None)

  def test_add_new_asset(self):
    # Add asset
    return_value = self.ns.add_new_asset(self.asset)
    self.assertTrue(return_value)

    # Test return data
    result = self.ns.search(self.asset.asset).data[0][0]
    self.assertEqual(self.asset.asset, result['asset'])
    self.assertEqual(self.asset.loopback, result['loopback'])
    self.assertEqual('JUNIPER', result['vendor'])
    self.assertEqual('BP0212512984', result['serial'])
    self.assertEqual('EX4200-48T', result['re0_model'])

    # Test add same asset again
    return_value = self.ns.add_new_asset(self.asset)
    self.assertFalse(return_value)

  def test_discover(self):
    # Test discover non-existing asset
    self.assertFalse(self.ns.discover(self.asset))

    # Test existing asset
    self.ns.add_new_asset(self.asset)
    self.assertTrue(self.ns.discover(self.asset))

  def test_update_interfaces(self):
    self.ns.add_new_asset(self.asset)

    mock_device = MockNetworkDevice('w-netlab-sw-4',
                                    loopback=None,
                                    groups='test_group',
                                    username='test_user',
                                    password='test_password',
                                    ssh_keyfile=None)

    new_interface = Interface('ge-0/0/1',
                              'Server 1',
                              '48:2C:6A:1E:59:3D',
                              1500)

    cursor = self.ns.update_interfaces(self.asset.asset, mock_device)
    self.assertEqual(1, cursor.matched_count)

    # Test empty interfaces
    mock_device.interfaces = []
    cursor = self.ns.update_interfaces(self.asset.asset, mock_device)
    self.assertEqual(1, cursor.matched_count)

  def test_extrace_device(self):
    # Single RE device
    device = netspot.NetSPOT._extract_device(DEVICE1_FACTS)
    self.assertEqual(device['hostname'], 'w-netlab-sw-4')
    self.assertEqual(device['model'], 'EX4200-48T')
    self.assertEqual(device['serial'], 'BP0212513097')
    self.assertEqual(device['version'], '14.1X53-D40.8')
    self.assertEqual(device.get('re0_model'), None)
    self.assertEqual(device.get('re0_version'), None)
    self.assertEqual(device.get('re1_model'), None)
    self.assertEqual(device.get('re1_version'), None)

    # Dual RE device
    device = netspot.NetSPOT._extract_device(DEVICE2_FACTS)
    self.assertEqual(device['hostname'], 'w-b080001-a-0')
    self.assertEqual(device['model'], 'Virtual Chassis')
    self.assertEqual(device['serial'], 'BP0212512984')
    self.assertEqual(device['version'], '12.2R4.5')

    self.assertEqual(device['re0_version'], '12.2R4.5')
    self.assertEqual(device['re1_version'], '12.2R4.6')

    self.assertEqual(device['re0_model'], 'EX4200-48T')
    self.assertEqual(device['re1_model'], 'EX4200-48PX')

    # 4 member switch stack, dual RE, RE0 and RE2
    device = netspot.NetSPOT._extract_device(DEVICE3_FACTS)
    self.assertEqual(device['re0_version'], '13.2X51-D36.0')
    self.assertEqual(device['re1_version'], '13.2X51-D36.1')
    self.assertEqual(device['re2_version'], '13.2X51-D36.2')
    self.assertEqual(device['re3_version'], '13.2X51-D36.3')

    self.assertEqual(device['re0_model'], 'EX4300-48T')
    self.assertEqual(device['re2_model'], 'EX4300-48P')
    self.assertEqual(device.get('re1_model'), None)


if __name__ == '__main__':
    unittest.main()
