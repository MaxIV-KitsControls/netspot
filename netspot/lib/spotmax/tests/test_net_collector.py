#!/usr/bin/python -tt
"""NetCollector tests

  Run: python -m unittest tests.test_net_collector

"""

import mock
import unittest

from collections import defaultdict

import net_collector



MACS = [{u'active': True,
         u'interface': u'ge-0/0/0.0',
         u'last_move': 0.0,
         u'mac': u'B8:27:EB:04:FF:A2',
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

ARP = [{'age': 647.0,
        'interface': u'me0.0',
        'ip': u'192.168.96.1',
        'mac': u'00:10:DB:FF:10:01'},
       {'age': 31.0,
        'interface': u'ge-0/0/0.0',
        'ip': u'192.168.31.1',
        'mac': u'B8:27:EB:04:FF:A2'}]


class MockDriver(object):
  def __init__(self, host, username, password):
    pass

  def open(self):
    return True

  def close(self):
    return True

  def get_mac_address_table(self):
    return MACS

  def get_arp_table(self):
    return ARP

class MockDevice(object):
  def cli(self, command):
    macs = """
        Ethernet switching table : 25 entries, 25 learned
        Routing instance : default-switch
            Vlan                MAC                 MAC         Age    Logical
            name                address             flags              interface
            srv-common-servers  00:11:0a:6b:da:d0   D             -   ae0.0
            srv-common-servers  *                   D             -   xe-0/0/7.0
            servers             00:50:56:94:31:4c   D             -   ge-0/0/1.0
        """

    return {'macs': macs}

class MockHelper(object):

  def resolv(self, hostname):
    return ['1.1.1.1']

  def CouldNotResolv(self):
    pass

class MockSpotMAX(object):
  def __init__(self, *args, **kwargs):
    self.database = 'database2'
    self.collection = 'blah'

  def _exist(ip, key=None):
    return None


def mock_get_network_driver(vendor):
  return MockDriver

class TestIPUsage(unittest.TestCase):
  def setUp(self):
    net_collector.get_network_driver = mock_get_network_driver
    net_collector.helpers = MockHelper()
    net_collector.MockSpotMAX = MockSpotMAX()

  def test_uppdate_ip(self):
    device = net_collector.NetCollector('testasset', 'username', 'password')
    device_macs = device.device_macs

    #ipu = net_collector.IPUsage(device_macs, 'TEST_DB', 'TEST_COLL')
    #ipu.uppdate_ip()

class TestNetCollector(unittest.TestCase):
  def setUp(self):
    net_collector.get_network_driver = mock_get_network_driver
    net_collector.helpers = MockHelper()

  def test_net_collector(self):
    devices = defaultdict()
    device = net_collector.NetCollector('testasset', 'username', 'password')

    device_macs = device.device_macs

    self.assertEqual('testasset', device_macs['asset'])
    self.assertEqual(2, len(device_macs['macs']))

    self.assertEqual('192.168.31.1', device_macs['macs'][0]['ip'])
    self.assertEqual(201, device_macs['macs'][0]['vlan'])
    self.assertEqual('B8:27:EB:04:FF:A2', device_macs['macs'][0]['mac'])

    self.assertEqual(None, device_macs['macs'][1]['ip'])
    self.assertEqual(0, device_macs['macs'][1]['vlan'])
    self.assertEqual('54:E0:32:30:87:01', device_macs['macs'][1]['mac'])

  def test_extract_macs(self):
    devices = defaultdict()
    nc = net_collector.NetCollector('testasset', 'username', 'password')
    device = MockDevice()

    # Populate MACS
    nc._get_mac_table(device)

    # Run _extract_macs
    nc._extract_macs()

    self.assertEqual(2, len(nc.device_macs))
    self.assertEqual({'interface': u'ge-0/0/0.0',
                      'ip': u'192.168.31.1',
                      'last_move': 0.0,
                      'mac': u'B8:27:EB:04:FF:A2',
                      'moves': 0,
                      'static': False,
                      'vlan': 201},
                      nc.device_macs['macs'][0])
    self.assertEqual({'interface': u'Router',
                      'ip': None,
                      'last_move': 0.0,
                      'mac': u'54:E0:32:30:87:01',
                      'moves': 0,
                      'static': True,
                      'vlan': 0},
                      nc.device_macs['macs'][1])

  def test_get_mac_table(self):
    devices = defaultdict()
    nc = net_collector.NetCollector('testasset', 'username', 'password')
    device = MockDevice()

    # Run
    nc._get_mac_table(device)

    # Number of MAC entries
    self.assertEqual(2, len(nc.macs))

    self.assertEqual('srv-common-servers', nc.macs[0]['vlan'])
    self.assertEqual(None, nc.macs[0]['last_move'])
    self.assertEqual('00:11:0A:6B:DA:D0', nc.macs[0]['mac'])
    self.assertEqual(False, nc.macs[0]['static'])
    self.assertEqual('ae0.0', nc.macs[0]['interface'])
    self.assertEqual(None, nc.macs[0]['moves'])

    self.assertEqual('servers', nc.macs[1]['vlan'])
    self.assertEqual(None, nc.macs[1]['last_move'])
    self.assertEqual('00:50:56:94:31:4C', nc.macs[1]['mac'])
    self.assertEqual(False, nc.macs[1]['static'])
    self.assertEqual('ge-0/0/1.0', nc.macs[1]['interface'])
    self.assertEqual(None, nc.macs[1]['moves'])


if __name__ == '__main__':
  unittest.main()
