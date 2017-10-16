#!/usr/bin/python -tt
"""JUNOS link down test

  Run: python -m unittest tests.test_spotmax

"""

import unittest
from spotmax import SpotMAX
from collections import defaultdict

class MockData(object):
  def __init__(self):
    self.data = defaultdict()

  def add(self, query):
    # Add asset/group
    if query.get('asset'):
      self.data[query['asset']] = query
    elif query.get('group'):
      self.data[query['group']] = query

  def get(self, key):
    # Return cursor
    cursor = MockCursor()

    # Add data to cursor if found
    data = self.data.get(key, None)
    if data:
      cursor.add_data(data)

    return cursor

  def delete(self, key):
    del(self.data[key])

  def __getitem__(self, asset):
    return self.data.get(asset, {})

class MockCursor(object):
  """Mocks a MongoDB cursor object."""

  def __init__(self):
    self.deleted_count = 0
    self.modified_count = 0
    self.matched_count = 0
    self.data_count = 0
    self.data = list()

  def add_data(self, data=None):
    """Add data to cursor."""
    self.data.append(data)
    self.data_count += 1

  def count(self):
    """Return number of items in cursor."""
    return self.data_count

  def get(self, key):
    """Return data or '' if not found."""
    return self.data.get(key, '')

  def limit(self, limit):
    """Ignore limit and return self."""
    return self

  def skip(self, limit):
    """Ignore skip and return self."""
    return self

  def __getitem__(self, index):
    """Makes the object indexable."""
    return self.data[index][0]

class MockCollection(object):
  def __init__(self):
    self.data = MockData()

  def _get_key(self, query):
    """Get key, either 'asset' or 'group'"""

    # Get asset name
    key = query.get('asset')

    # If not key, check if this is a group query
    if not key:
      key = query.get('group')

    return key

  def find(self, query):
    # Get asset name
    key = query.get('asset')

    # If not key, check if this is a group query
    if not key:
      key = query.get('group')

    # Check if asset is empty and if query is in "or" form
    # Eg. {'$or': [{'asset': {'$regex': 'test_asset'}}, {'interfaces.asset': {'$regex': 'test_asset'}}, {'macs.asset': {'$regex': 'test_asset'}}]}
    if not key and '$or' in query.keys():
      key = query['$or'][0]['asset']['$regex']

    # If asset is set return MockCursor with the entry
    # Otherwise return empty MockCursor
    if key:
      cursor = MockCursor()

      # Find asset
      if self.data.get(key).data:
        cursor.add_data(self.data.get(key).data)

      return cursor
    else:
      return MockCursor()

  def find_and_modify(self, query=None, update=None, upsert=None):
    key = self._get_key(query)

    for updates in update:
      for variable in update[updates]:
        name = variable.split('.')[2]
        value = update[updates][variable]
        data = {name: value}

        if data in self.data[key].get('variables', []):
          return None
        else:
          # Add variables if missing
          if not self.data[key].get('variables'):
            self.data[key]['variables'] = list()

          self.data[key]['variables'].append(data)
          return True

  def find_one(self, query):
    key = self._get_key(query)

    if self.data.get(key):
      return self.data[key]
    else:
      return MockData()

  def insert_one(self, asset):
    self.data.add(asset)

  def update_one(self, query=None, update=None):
    key = self._get_key(query)

    cursor = MockCursor()

    # Push / add action
    if update.get('$push'):
      name = update['$push']['variables'].keys()[0]
      value = update['$push']['variables'][name]
      self.data[key]['variables'].append({name: value})
    # Remove action
    elif update.get('$pull'):
      name = update['$pull']['variables'].keys()[0]
      value = update['$pull']['variables'][name]
      self.data[key]['variables'].remove({name: value})
      # Set modified
      cursor.modified_count = 1
    elif update.get('$set'):
      for data_key in update['$set'].keys():
        self.data.data[key][data_key] = update['$set'][data_key]
      cursor.matched_count = 1

    # Return cursor
    return cursor

  def delete_one(self, query=None):
    asset = query['asset']
    cursor = MockCursor()

    # Delete data if found. Otherwise return empty cursor
    if self.data.get(asset).count() > 0:
      self.data.delete(asset)
      cursor.deleted_count = 1

    return cursor

class TestSPOTMAX(unittest.TestCase):
 
  def setUp(self):
    self.sm = SpotMAX(None, None)
    self.sm.collection = MockCollection()

  def test_add_variable(self):
    # Asset does not exist
    self.assertFalse(self.sm.add_variable('asset', 'test_asset', 'TEST_VAR:TEST_VALUE'))

    # Add asset
    self.sm.collection.data.add({'asset': 'test_asset', 'variables': []})

    # Test adding new variable
    self.assertTrue(self.sm.add_variable('asset', 'test_asset', 'TEST_VAR:NEW_VALUE'))

    # Test modifying new variable
    self.assertTrue(self.sm.add_variable('asset', 'test_asset', 'TEST_VAR:MOD_VALUE'))

  def test_delete(self):
    asset = 'test_asset'

    # Delete non-existing asset
    self.assertFalse(self.sm.delete(asset, key='asset'))

    # Add asset and test
    self.sm.collection.data.add({'asset': 'test_asset', 'variables': []})
    self.assertTrue(self.sm.delete(asset, key='asset'))

  def test_delete_variable(self):
    asset = 'test_asset'
    variable = 'TEST_VAR:TEST_VALUE'

    # Asset doesn't exist
    self.assertFalse(self.sm.delete_variable(asset, variable, 'asset'))

    # Add asset and variable
    self.sm.collection.data.add({'asset': 'test_asset', 'variables': []})
    self.sm.add_variable('asset', 'test_asset', variable)
    self.assertTrue(self.sm.delete_variable(asset, 'TEST_VAR', 'asset'))

  def test_exist(self):
    asset = 'test_asset'

    # Non-existing asset
    self.assertFalse(self.sm._exist(asset, key='asset'))

    # Add asset and test
    self.sm.collection.data.add({'asset': 'test_asset', 'variables': []})
    self.assertTrue(self.sm._exist(asset, key='asset'))

  def test_parse_search_term(self):
    # Asset name
    self.assertEqual((None, 'router_name'), SpotMAX().parse_variable('router_name'))
    self.assertNotEqual((None, 'router_name'), SpotMAX().parse_variable('router_name2'))

    # Key and value search
    self.assertEqual(('group', 'white'), SpotMAX().parse_variable('group:white'))
    self.assertEqual(('group', 'white:blue'), SpotMAX().parse_variable('group:white:blue'))
    self.assertEqual(('mac', 'B0:A8:6E:0C:5C:2B'), SpotMAX().parse_variable('mac:b0:a8:6e:0c:5c:2b'))
    self.assertEqual(('interface', 'ge-0/0/12'), SpotMAX().parse_variable('interface:ge-0/0/12'))
    self.assertEqual(('version', '14.1X53-D40.8'), SpotMAX().parse_variable('version:14.1X53-D40.8'))

    # Misspelled key value search
    self.assertEqual(('group', ':white'), SpotMAX().parse_variable('group::white'))

  def test_search(self):
    asset = 'test_asset'

    # Search empty database
    self.assertEqual(0, self.sm.search(asset).count())

    # Add asset
    self.sm.collection.data.add({'asset': 'test_asset', 'variables': []})
    self.assertEqual([{'variables': [], 'asset': 'test_asset'}], self.sm.search(asset).data[0])

    # Add variable
    self.assertTrue(self.sm.add_variable('asset', 'test_asset', 'TEST_VAR:NEW_VALUE'))
    self.assertEqual([{'variables': [{'TEST_VAR': 'NEW_VALUE'}], 'asset': 'test_asset'}],
                     self.sm.search(asset).data[0])

    # Test non-existing asset again
    self.assertEqual(0, self.sm.search('empty_again').count())


if __name__ == '__main__':
    unittest.main()