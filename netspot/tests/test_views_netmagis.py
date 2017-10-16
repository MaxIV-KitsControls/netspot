#!/usr/bin/python -tt

# Run: python manage.py test netspot.tests.test_views_netmagis

import netspot.views_netmagis as views_netmagis
import datetime

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class MockNetSPOT(object):
  def __init__(self, database=None, collection=None):
    pass

  def search(self, search, key=None, sort=None):
    return [{u'lastModified': datetime.datetime(2017, 9, 8, 10, 1, 11, 161000),
             u'_id': '58eb78dde79d524a3f6163f3',
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
              u'w-e110032-a-2'},
             {u'lastModified': datetime.datetime(2017, 9, 8, 10, 1, 38, 291000),
              u'_id': '59086a97e79d526a5d261c0f',
              u'macs': [{u'ip': u'194.47.254.175',
                         u'vlan': None,
                         u'last_move': None,
                         u'mac': u'00:00:48:42:71:E7',
                         u'static': None,
                         u'interface': u'reth1.2205',
                         u'moves': None},
                        {u'ip': u'192.168.73.114',
                         u'vlan': None,
                         u'last_move': None,
                         u'mac': u'6C:88:14:67:BA:04',
                         u'static': None,
                         u'interface': u'reth1.2200',
                         u'moves': None}],
              u'asset':
              u'w-kirk01-fw-0'}]

class MockNetMagisDB(object):

  def __enter__(self):
    return self

  def __exit__(self, ex_type, ex_value, traceback):
    pass

  def search(self, search):
    if search:
      return [{u'comment': 'Poster printer', u'name': 'w-e120072-prt-0', u'mac': '00:00:48:42:71:e7', u'date': datetime.datetime(2016, 3, 1, 10, 21, 19), u'idrr': 6340, u'addr': '192.168.25.25'}]
    else:
      return []

class QuestionIndexViewTests(TestCase):

  def setUp(self):
    # Test user
    User.objects.create_user(username='testuser', password='secretpassword')

    # Override netspot and NetMagisDB
    views_netmagis.netspot.NetSPOT = MockNetSPOT
    views_netmagis.nm_helper.NetMagisDB = MockNetMagisDB

  def test_searchhost(self):
    # Try without authentication
    response = self.client.post(reverse('nm_searchhost'), {})

    # Not logged in. Should return redirect
    self.assertRedirects(response, '/login/?next=/nm/searchhost')
    self.assertEqual(response.status_code, 302)

    # Try with authentication
    self.client.login(username='testuser', password='secretpassword')

    # Empty search
    response = self.client.post(reverse('nm_searchhost'), {})
    self.assertEqual(response.context[u'mac_search'], [])
    self.assertEqual(response.context[u'hosts'], [])
    self.assertEqual(response.context[u'search'], None)

    # Test search for "posterprt"
    search = 'posterprt'
    response = self.client.post(reverse('nm_searchhost'), {'search': search})

    self.assertEqual(len(response.context[u'mac_search']), 2)
    self.assertEqual(response.context[u'mac_search'][0]['mac'], '00:00:48:42:71:E7')
    self.assertEqual(response.context[u'mac_search'][0]['ip'], None)
    self.assertEqual(response.context[u'mac_search'][0]['interface'], u'ge-7/0/13.0')
    self.assertEqual(response.context[u'mac_search'][1]['mac'], '00:00:48:42:71:E7')
    self.assertEqual(response.context[u'mac_search'][1]['ip'], u'194.47.254.175')
    self.assertEqual(response.context[u'mac_search'][1]['interface'], u'reth1.2205')

    self.assertEqual(len(response.context[u'hosts']), 1)
    self.assertEqual(response.context[u'hosts'][0]['addr'], '192.168.25.25')
    self.assertEqual(response.context[u'hosts'][0]['idrr'], 6340)
    self.assertEqual(response.context[u'hosts'][0]['mac'], '00:00:48:42:71:e7')

    self.assertEqual(response.context[u'search'], search)
