#!/usr/bin/python -tt
"""JUNOS link down test

  Run: python -m unittest tests.test_network_device

"""

import unittest
import network_device

VLAN_INTERFACES = """  Untagged interfaces: ge-0/0/0.0, ge-0/0/1.0,
                        ge-0/0/46.0, ge-0/0/47.0, xe-2/0/0.0
                        Tagged interfaces: ae0.0*
                        """

VLAN_DETAIL = """VLAN: acc-wlan-client-staff, 802.1Q Tag: 2200, Admin State: Enabled
                  Number of interfaces: 1 (Active = 1)
                    Tagged interfaces: ae0.0*

                  VLAN: default, 802.1Q Tag: Untagged, Admin State: Enabled

                  VLAN: mac-radius-dummy, 802.1Q Tag: 3999, Admin State: Enabled
                  Number of interfaces: 43 (Active = 12)
                    Untagged interfaces: ge-0/0/0.0, ge-0/0/43.0, ge-0/0/44.0, ge-0/0/45.0,
                    ge-0/0/46.0, ge-0/0/47.0, ge-1/0/0.0
                    Tagged interfaces: ae0.0*
                    """

VLAN_DETAIL_QFX = """Routing instance: default-switch
                        VLAN Name: acc-staff-client-three         State: Active
                      Tag: 2210 
                      Internal index: 8, Generation Index: 9, Origin: Static
                      MAC aging time: 300 seconds
                      Interfaces:
                          ae0.0*,tagged,trunk
                      Number of interfaces: Tagged 1    , Untagged 0    
                      Total MAC count: 67 

                      Routing instance: default-switch
                        VLAN Name: net-management                 State: Active
                      Tag: 2010 
                      Internal index: 2, Generation Index: 2, Origin: Static
                      MAC aging time: 300 seconds
                      Layer 3 interface: irb.2010
                      Interfaces:
                          ae0.0*,tagged,trunk
                      Number of interfaces: Tagged 1    , Untagged 0    
                      Total MAC count: 13 

                      Routing instance: default-switch
                        VLAN Name: san-mgmt                       State: Active
                      Tag: 2045 
                      Internal index: 3, Generation Index: 3, Origin: Static
                      MAC aging time: 300 seconds
                      Interfaces:
                          ae0.0*,tagged,trunk
                      Number of interfaces: Tagged 1    , Untagged 0    
                      Total MAC count: 8 

                      Routing instance: default-switch
                        VLAN Name: srv-cluster                    State: Active
                      Tag: 2051 
                      Internal index: 7, Generation Index: 8, Origin: Static
                      MAC aging time: 300 seconds
                      Interfaces:
                          ae0.0*,tagged,trunk
                          xe-0/0/10.0*,untagged,access
                          xe-0/0/11.0*,untagged,access
                          xe-0/0/37.0*,untagged,access
                          xe-0/0/8.0*,untagged,access
                      Number of interfaces: Tagged 1    , Untagged 4    
                      Total MAC count: 30 

                      Routing instance: default-switch
                        VLAN Name: srv-common-servers             State: Active
                      Tag: 2030 
                      Internal index: 4, Generation Index: 4, Origin: Static
                      MAC aging time: 300 seconds
                      Interfaces:
                          ae0.0*,tagged,trunk
                      Number of interfaces: Tagged 1    , Untagged 0    
                      Total MAC count: 19 

                      Routing instance: default-switch
                        VLAN Name: srv-gpfs                       State: Active
                      Tag: 2046                               
                      Internal index: 5, Generation Index: 5, Origin: Static
                      MAC aging time: 300 seconds
                      Interfaces:
                          ae0.0*,tagged,trunk
                          ae3.0,untagged,access
                          ae4.0,untagged,access
                          xe-0/0/38.0*,untagged,access
                          xe-0/0/39.0*,untagged,access
                          xe-0/0/40.0*,untagged,access
                          xe-0/0/41.0*,untagged,access
                      Number of interfaces: Tagged 1    , Untagged 6    
                      Total MAC count: 2 

                      Routing instance: default-switch
                        VLAN Name: srv-gpfs-lunarc                State: Active
                      Tag: 2047 
                      Internal index: 9, Generation Index: 10, Origin: Static
                      MAC aging time: 300 seconds
                      Interfaces:
                          ae0.0*,tagged,trunk
                          xe-0/0/24.0*,untagged,access
                          xe-0/0/25.0*,untagged,access
                          xe-0/0/26.0*,untagged,access
                      Number of interfaces: Tagged 1    , Untagged 3    
                      Total MAC count: 5 

                      Routing instance: default-switch
                        VLAN Name: srv-internal-servers           State: Active
                      Tag: 2031 
                      Internal index: 6, Generation Index: 6, Origin: Static
                      MAC aging time: 300 seconds
                      Interfaces:
                          ae0.0*,tagged,trunk
                          ae1.0*,untagged,access
                          ae2.0*,untagged,access
                          ae5.0,untagged,access
                          ae6.0,untagged,access
                          xe-0/0/12.0*,untagged,access
                          xe-0/0/13.0*,untagged,access
                          xe-0/0/9.0*,untagged,access
                      Number of interfaces: Tagged 1    , Untagged 7    
                      Total MAC count: 45 

                      Routing instance: default-switch
                        VLAN Name: srv-lunarc                     State: Active
                      Tag: 2052 
                      Internal index: 10, Generation Index: 11, Origin: Static
                      MAC aging time: 300 seconds
                      Interfaces:
                          ae0.0*,tagged,trunk
                          ae7.0,untagged,access
                          ae8.0,untagged,access
                      Number of interfaces: Tagged 1    , Untagged 2    
                      Total MAC count: 0

                      """


class MockPhyPortTable(object):
  def __init__(self, device):
    pass

  def get(self):
    return []


class MockDriver(object):
  def __init__(self, host, user, password, ssh_private_key_file=None):
    self.facts = {'model': 'EX4800-PS3'}
    self.interfaces = dict()
    self.lldp_neighbors = dict()

  def open(self):
    return True

  def close(self):
    return True

  def get_facts(self):
    return self.facts

  def get_interfaces(self):
    return self.interfaces

  def get_lldp_neighbors(self):
    return self.lldp_neighbors

  def cli(self, command):
    return {command[0]: ''}


def mock_device():
  return MockDriver('127.0.0.1', 'username', 'password')

def mock_get_network_driver(os):
  return MockDriver

class TestSPOTMAX(unittest.TestCase):

  def setUp(self):
    network_device.get_network_driver = mock_get_network_driver
    self.device = network_device.NetworkDevice('127.0.0.1')

  def test_parse_search_term(self):
    self.assertEqual('127.0.0.1', self.device.ip_address)

  def test_get_vlan_information(self):
    self.device.get_vlan_information(VLAN_DETAIL)

    self.assertEqual(3, len(self.device.vlans))

    self.assertEqual('2200', self.device.vlans[0]['vlan'])
    self.assertEqual('acc-wlan-client-staff', self.device.vlans[0]['name'])
    self.assertEqual(['ae0'], self.device.vlans[0]['tagged_interfaces'])
    self.assertEqual([], self.device.vlans[0]['untagged_interfaces'])

    self.assertEqual('3999', self.device.vlans[2]['vlan'])
    self.assertEqual('mac-radius-dummy', self.device.vlans[2]['name'])
    self.assertEqual(['ae0'], self.device.vlans[2]['tagged_interfaces'])
    self.assertEqual(['ge-0/0/0', 'ge-0/0/43', 'ge-0/0/44', 'ge-0/0/45', 'ge-0/0/46', 'ge-0/0/47', 'ge-1/0/0'],
                     self.device.vlans[2]['untagged_interfaces'])

  def test_get_vlan_information_qfx(self):
    self.device.get_vlan_information_qfx(VLAN_DETAIL_QFX)
    self.assertEqual(9, len(self.device.vlans))

    self.assertEqual('2210', self.device.vlans[0]['vlan'])
    self.assertEqual('acc-staff-client-three', self.device.vlans[0]['name'])
    self.assertEqual(['ae0'], self.device.vlans[0]['tagged_interfaces'])
    self.assertEqual([], self.device.vlans[0]['untagged_interfaces'])

    self.assertEqual('2031', self.device.vlans[7]['vlan'])
    self.assertEqual('srv-internal-servers', self.device.vlans[7]['name'])
    self.assertEqual(['ae0'], self.device.vlans[7]['tagged_interfaces'])
    self.assertEqual(['ae1', 'ae2', 'ae5', 'ae6', 'xe-0/0/12', 'xe-0/0/13', 'xe-0/0/9'], self.device.vlans[7]['untagged_interfaces'])

  def test_get_interfaces_per_vlan(self):
    untagged, tagged = self.device.get_interfaces_per_vlan(VLAN_INTERFACES)
    self.assertEqual(5, len(untagged))
    self.assertEqual(1, len(tagged))

  def test_clean_interface(self):
    self.assertEqual('ge-0/0/1', self.device.clean_interface('ge-0/0/1*'))
    self.assertEqual('ge-0/0/1', self.device.clean_interface('ge-0/0/1,'))
    self.assertEqual('ge-0/0/1', self.device.clean_interface('ge-0/0/1.0'))
    self.assertEqual('ge-0/0/1', self.device.clean_interface('ge-0/0/1\n'))

if __name__ == '__main__':
  unittest.main()
