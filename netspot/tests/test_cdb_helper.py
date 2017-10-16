#!/usr/bin/python -tt
"""cdb_hepler tests

  Run: python -m unittest tests.test_cdb_helper

"""

import unittest

import cdb_helper


class TestCDBHelper(unittest.TestCase):
  def setUp(self):
    pass

  def test_get_interface(self):
    # Test leading 0
    cable_path = [['blah', 'ASW-01', 'ETH_OUT08']]
    interface = cdb_helper.get_interface(cable_path)
    self.assertEqual('ge-0/0/8', interface)

    # Test without leading 0
    cable_path = [['blah', 'ASW-01', 'ETH_OUT18']]
    interface = cdb_helper.get_interface(cable_path)
    self.assertEqual('ge-0/0/18', interface)

    # Test FPC 1
    cable_path = [['blah', 'ASW-02', 'ETH_OUT18']]
    interface = cdb_helper.get_interface(cable_path)
    self.assertEqual('ge-1/0/18', interface)

    # Test endpoint as the first item in the list
    cable_path = [['test:', 'B303A-A100377-CAB02-NET-ASW-03', 'ETH_OUT16', 'NETWORK-02'],
                  ['test:', 'B303A-A100383-NET-NO-08', 'eth_IN01']]
    interface = cdb_helper.get_interface(cable_path)
    self.assertEqual('ge-2/0/16', interface)

  def test_get_search_term(self):
    # Test white e110032
    cable_path = [[u'Equipment & Channel:', u'S-E110059-NET-NO-01', u'eth_IN01'],
                  ['Cable:', 16794L],
                  ['Equipment & Channel:', 'S-E110032-CAB06-NET-PP-37', 'ETH_IN15', 'NETWORK-03'],
                  ['Equipment & Channel:', 'S-E110032-CAB06-NET-PP-37', 'ETH_OUT15'],
                  ['Cable:', 14596L], ['Equipment & Channel:', 'S-E110032-CAB16-NET-ASW-03', 'ETH_OUT14', 'NETWORK-03']]
    search = cdb_helper.get_search_term(cable_path)
    self.assertEqual('w-e110032', search)

    # Test blue e110032
    cable_path = [[u'Equipment & Channel:', u'S-E110059-NET-NO-01', u'eth_IN01'],
                  ['Cable:', 16794L],
                  ['Equipment & Channel:', 'S-E110032-CAB06-NET-PP-37', 'ETH_IN15', 'NETWORK-02'],
                  ['Equipment & Channel:', 'S-E110032-CAB06-NET-PP-37', 'ETH_OUT15'],
                  ['Cable:', 14596L], ['Equipment & Channel:', 'S-E110032-CAB16-NET-ASW-03', 'ETH_OUT14', 'NETWORK-02']]
    search = cdb_helper.get_search_term(cable_path)
    self.assertEqual('b-e110032', search)

    # Test green e110032
    cable_path = [[u'Equipment & Channel:', u'S-E110059-NET-NO-01', u'eth_IN01'],
                  ['Cable:', 16794L],
                  ['Equipment & Channel:', 'S-E110032-CAB06-NET-PP-37', 'ETH_IN15', 'NETWORK-01'],
                  ['Equipment & Channel:', 'S-E110032-CAB06-NET-PP-37', 'ETH_OUT15'],
                  ['Cable:', 14596L], ['Equipment & Channel:', 'S-E110032-CAB16-NET-ASW-03', 'ETH_OUT14', 'NETWORK-01']]
    search = cdb_helper.get_search_term(cable_path)
    self.assertEqual('g-e110032', search)

  def test_get_outlet_port_code(self):
    # Lower case correct input
    port, code = cdb_helper.get_outlet_port_code('s-e110059-no-01_in01')
    self.assertEqual('eth_IN01', port)
    self.assertEqual('S-E110059-NET-NO-01', code)

    # Upper case correct input
    port, code = cdb_helper.get_outlet_port_code('B303A-A100383-NO-08_IN01')
    self.assertEqual('eth_IN01', port)
    self.assertEqual('B303A-A100383-NET-NO-08', code)

    # Test patch panel port
    port, code = cdb_helper.get_outlet_port_code('B112A-D101230-CAB10-PP-01_IN02')
    self.assertEqual('eth_IN02', port)
    self.assertEqual('B112A-D101230-CAB10-NET-PP-01', code)
    port, code = cdb_helper.get_outlet_port_code('R3-A110211-CAB02-NET-PP-01-ETH_OUT11')
    self.assertEqual('eth_out11', port)
    self.assertEqual('R3-A110211-CAB02-NET-PP-01', code)

    # Incorrect input
    port, code = cdb_helper.get_outlet_port_code('INCORRECT-INPUT')
    self.assertEqual('', port)
    self.assertEqual('', code)

    port, code = cdb_helper.get_outlet_port_code('B303A-A100377-CAB02-ASW-03_OUT16')
    self.assertEqual('eth_OUT16', port)
    self.assertEqual('B303A-A100377-CAB02-NET-ASW-03', code)

if __name__ == '__main__':
  unittest.main()
