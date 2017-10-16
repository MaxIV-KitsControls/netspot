#!/usr/bin/python -tt
"""ts_lib tests

  Run: python -m unittest tests.test_helpers

"""

import unittest

from helpers import get_dhcp_server


class TestHelpers(unittest.TestCase):
  def setUp(self):
    pass

  def test_get_dhcp_server(self):
    self.assertEqual('172.16.2.10', get_dhcp_server(network='blue'))
    self.assertEqual('10.0.2.10', get_dhcp_server(network='green'))
    self.assertEqual('194.47.252.134', get_dhcp_server(network='white'))
    self.assertEqual(None, get_dhcp_server(network='yellow'))

    self.assertEqual('172.16.2.10', get_dhcp_server(asset='b-a3313131-g-4'))
    self.assertEqual('10.0.2.10', get_dhcp_server(asset='g-a878fdsf-b-4'))
    self.assertEqual('194.47.252.134', get_dhcp_server(asset='w-a878797-b-4'))
    self.assertEqual(None, get_dhcp_server(asset='y-a8798789-a'))
 
    self.assertEqual('172.16.2.10', get_dhcp_server(network='blue', asset='g-a878fdsf-b-4'))
    self.assertEqual(None, get_dhcp_server(network='yellow', asset='y-a878fdsf-b-4'))

if __name__ == '__main__':
  unittest.main()
