#!/usr/bin/python -tt

# Run: python manage.py test netspot.tests.test_views_pa

import netspot.views_pa as views_pa

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from netspot.models import ConfigurationTemplate, Category, Playbook, PlaybookPermission


CABLE_PATH = [[u'Equipment & Channel:', 'S-E110059-NET-NO-01', 'eth_IN01'],
              ['Cable:', 16794L],
              ['Equipment & Channel:', 'S-E110032-CAB06-NET-PP-37', 'ETH_IN15', 'NETWORK-03'],
              ['Equipment & Channel:', 'S-E110032-CAB06-NET-PP-37', 'ETH_OUT15'],
              ['Cable:', 14596L],
              ['Equipment & Channel:', 'S-E110032-CAB16-NET-ASW-03', 'ETH_OUT14', 'NETWORK-02']]

def mock_get_outlet_port_code(outlet):
  """Mock cdb_helper.get_outlet_port_code"""

  return ('eth_IN01', 'S-E110059-NET-NO-01')

def mock_get_search_term(cable_path):
  """Mock cdb_helper.get_search_term"""

  return 'e110032'

def mock_get_interface(cable_path):
  """Mock cdb_helper.get_interface"""

  return 'ge-2/0/15'

def mock_get_cable_connected_to_equipment_channel(outlet_code,
                                                  outlet_port,
                                                  cable_path,
                                                  lc_port=False,
                                                  debug=False):
  """Mock cdb_helper.get_cable_connected_to_equipment_channel"""

  for sub_path in CABLE_PATH:
    cable_path.append(sub_path)

class MockNSObject(object):
  """Mock NetSPOT object."""

  def __init__(self):
    self.data = [{u'_id': '58eb78dde79d524a3f6163f3',
                  u'macs': [{u'ip': None,
                             u'vlan': u'net-wlan-mgmt',
                             u'last_move': None,
                             u'mac': u'00:00:48:42:71:E7',
                             u'static': False,
                             u'interface': u'ge-7/0/13.0',
                             u'moves': None},
                            {u'ip': None,
                             u'vlan': u'acc-voip-ldc',
                             u'last_move': None,
                             u'mac': u'00:1B:4F:33:6A:0B',
                             u'static': False,
                             u'interface': u'ae0.0',
                             u'moves': None},
                            {u'ip': None,
                             u'vlan': u'net-wlan-mgmt',
                             u'last_move': None,
                             u'mac': u'40:B4:F0:26:7A:C0',
                             u'static': False,
                             u'interface': u'ae0.0',
                             u'moves': None}],
                  u'asset':
                  u'w-e110032-a-1'}]

  def __getitem__(self, index):
    return self.data[index]

  def count(self):
    return len(self.data)

class MockNetSPOT(object):
  """Mock NetSPOT."""
  def __init__(self, database=None, collection=None):
    pass

  def search(self, search, key=None, sort=None):
    return MockNSObject()

class QuestionIndexViewTests(TestCase):

  def setUp(self):
    # Authenticate
    User.objects.create_user(username='testuser', password='secretpassword')
    self.client.login(username='testuser', password='secretpassword')

    # PLaybook
    pb_permission = PlaybookPermission.objects.create(name='test_group',
                                                      users='testuser')
    playbook = Playbook.objects.create(name='test_playbook',
                                       playbook_file='test_playbook_file',
                                       user_auth=False,
                                       template_input=True,
                                       permissions=pb_permission)

    # Configuration Template
    category = Category.objects.create(name='test_category')
    ConfigurationTemplate.objects.create(name='test_template',
                                         category=category,
                                         playbook=playbook)

    # Override cdb_helper
    views_pa.cdb_helper.get_outlet_port_code = mock_get_outlet_port_code
    views_pa.cdb_helper.get_search_term = mock_get_search_term
    views_pa.cdb_helper.get_interface = mock_get_interface
    views_pa.cdb_helper.get_cable_connected_to_equipment_channel = mock_get_cable_connected_to_equipment_channel

    # Override NetSPOT
    views_pa.netspot.NetSPOT = MockNetSPOT

  def test_pa_prepare(self):
    # Test non beamline circuit
    response = self.client.post(reverse('pa_prepare'), {'outlet': 's-e110059-no-01_in01',
                                                        'template_id': 1})

    self.assertEqual(response.context['outlet'], 's-e110059-no-01_in01')
    self.assertEqual(response.context['beamline'], '')
    self.assertEqual(response.context['asset'], 'w-e110032-a-1')
    self.assertEqual(response.context['interfaces'], 'ge-2/0/15')
    self.assertEqual(response.context['cable_path'], [[u'Equipment & Channel:', 'S-E110059-NET-NO-01', 'eth_IN01'],
                                                      [u'Equipment & Channel:', 'S-E110059-NET-NO-01', 'eth_IN01'],
                                                      ['Cable:', 16794L],
                                                      ['Equipment & Channel:', 'S-E110032-CAB06-NET-PP-37', 'ETH_IN15', 'NETWORK-03'],
                                                      ['Equipment & Channel:', 'S-E110032-CAB06-NET-PP-37', 'ETH_OUT15'],
                                                      ['Cable:', 14596L],
                                                      ['Equipment & Channel:', 'S-E110032-CAB16-NET-ASW-03', 'ETH_OUT14', 'NETWORK-02']])
