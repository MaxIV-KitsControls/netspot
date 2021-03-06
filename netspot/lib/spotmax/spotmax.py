#!/usr/bin/python -tt

"""Module to connect to MongoDB. Acts as base class for different SPOTs. eg netspot."""

from bson.objectid import ObjectId

from pymongo import MongoClient
from datetime import datetime

import netspot_settings


class SpotMAX(object):
  """Class that provides database access."""

  def __init__(self, database=None, collection=None):

    if database and collection:
      # Connect to inventory
      self.client = MongoClient()          # Defaults to localhost on port 27017

      # Select correct database
      self.database = self.client[database]
      self.database.authenticate(netspot_settings.DB_USERNAME, netspot_settings.DB_PASSWORD)

      # Select collection
      self.collection = self.database[collection]
    else:
      self.client = None
      self.database = None
      self.collection = None

  def __exit__(self, exc_type, exc_value, traceback):
    """Cloase connection to MongoDB."""
    self.client.close()

  def add_variable(self, target, name=None, variable=None):
    """Add or update name variable.

    Args:
      name: string, name of the asset/group
      variable: string, variable:value eg. model:EX4200
      target: string, either 'asset' or 'group'

    Returns:
      Boolean: True if added/modified, False if target doesn't exist
    """

    if self._exist(name, key=target):
      # Get variable key and value
      key, value = self.parse_variable(variable)

      # Modify variable if it exist
      result = self.collection.find_and_modify(
          query={target: name, 'variables.' + key: {'$exists': True}},
          update={'$set': {"variables" + ".$." + key : value}}, upsert=False)

      # Add new variable if variable doesn't exist
      if result is None:
        result = self.collection.update_one({target: name},
                                            {'$push': {'variables' : {key: value}}})

      return True
    else:
      return False

  def count(self):
    """Return the number of documents in collection."""

    return self.collection.count()

  def delete_variable(self, name, variable, target):
    """Delete variable from either host or group.

    Args:
      name: string, name of the asset/group
      variable: string, variable name
      target: string, either 'asset' or 'group'

    Returns:
      Boolean: True, if deleted
               False, if asset/group not found
    """

    if self._exist(name, key=target):
      # Need to get value in order to be able to remove the item
      result = self.collection.find_one({target: name})

      for var in result['variables']:
        if variable in var.keys():
          value = var[variable]
          break

      result = self.collection.update_one({target: name},
                                          {'$pull': {'variables': {variable: value}}})
      if result.modified_count:
        return True
    else:
      return False

  def parse_variable(self, variable):
    """Parse variable term eg. model:EX4200

    Args:
      variable: string, search term

    Returns:
      (key, value): tuple, key: DB field name
                           value: DB field value
    """

    variable = variable.strip()

    # Split search if input is key:value eg. groups:my_group
    if ':' in variable:
      # Key is the string before the first ':'
      key = variable.split(':')[0]

      # Value could contain more ':'
      value = ':'.join(variable.split(':')[1:])
    else:
      key = None
      value = variable

    # Convert MAC to upper case
    if key == 'mac':
      value = value.upper()

    return (key, value)

  def delete(self, name, key='asset'):
    """Delete asset or group.

    Args:
      name: string, asset/group name
      key: string, either 'asset' or 'group'

    Returns:
      Boolean:  True if success
                False if failed
    """

    # Try to delete asset
    cursor = self.collection.delete_one({key: name})

    if cursor.deleted_count == 1:
      return True
    else:
      return False

  def _exist(self, name, key='asset'):
    """Check if name exist. Returns True or False.

    Args:
      name: string, name of the asset or group
      key: string, either 'asset' or 'group'

    Returns:
      boolean: True if found, false if not found.
    """

    cursor = self.collection.find({key: name})

    if cursor.count() == 0:
      return False
    else:
      return True

  def search(self, searchterm, key='asset', sort=None, limit=100, page=1):
    """Search inventory based on searchterm.

      Args:
        searchterm: string, what to search for
        key: string, either asset or group

      Returns:
        return_cursor: MongoDB cursor
    """

    # Parse search term
    field, value = self.parse_variable(searchterm.strip())

    # Split if comma separated list
    values = set(value.split(','))

    # Check if field is set, otherwise set it to key
    if not field:
      field = key

    # Search both top level field and 'interfaces' fields
    search_list = list()
    for search_value in values:
      search_dict = {field: {'$regex': search_value}}
      search_list.append(search_dict)

    # Add interfaces and MACs
    search_list.append({'interfaces.%s' % field: {'$regex': value}})
    search_list.append({'macs.%s' % field: {'$regex': value}})

    # Get assets
    cursor = self.collection.find({'$or': search_list}).skip(limit*(page-1)).limit(limit)

    # Sort if sort is specified
    if sort:
      cursor = cursor.sort(sort)

    return cursor


class SPOTGroup(SpotMAX):
  """Class that interacts with the MongoDB backend."""

  def __init__(self, database=netspot_settings.DATABASE, collection=netspot_settings.COLL_NETSPOT_GROUPS):
    SpotMAX.__init__(self, database, collection)

  def add_group(self, group):
    """Add new group.

    Args:
      group: string, name of group

    Returns:
      Boolean: True, added successfully
               False, not added
    """

    # Check if group exists already
    if self._exist(group, key='group'):
      return False

    # Add group to database
    self.collection.insert_one({'group': group})
    return True

  def get_variables(self, group):
    """Returns all variables for a given group.

    Args:
      group: string, group name

    Returns:
      variables: list of dicts, eg. [{'var1': 'val1'}, {'var2': 'val2'}]
    """

    # Get group
    cursor = self.collection.find({'group': group})

    try:
      result = cursor[0]['variables']
    except (KeyError, IndexError):
      result = []

    # Return
    return result

class SPOTLog(SpotMAX):
  """Class to log playbook runs."""

  def __init__(self,
               database=netspot_settings.DATABASE,
               collection=netspot_settings.COLL_PLAYBOOK_LOGS):

    SpotMAX.__init__(self, database, collection)

  def get_log_entries(self, limit=10):
    """Return X number of log entries."""

    return self.collection.find().limit(limit).sort([('date', -1), ('time', -1)])

  def get_log_entry(self, log_id):
    """Find log entry on '_id'."""

    return self.collection.find_one({'_id': ObjectId(log_id)})

  def log(self,
          username=None,
          playbook=None,
          search_filter=None,
          arguments=None,
          runtime=None,
          success=None,
          output=None):
    """Write log to database."""

    # Get time and date
    now = datetime.now()

    # Create log entry
    log_entry = {'username': username,
                 'playbook': playbook,
                 'date': now.strftime("%Y-%m-%d"),
                 'time': now.strftime("%H:%M"),
                 'filter': search_filter,
                 'arguments': arguments,
                 'runtime': runtime,
                 'success': success,
                 'output': output
                }

    # Save to database
    self.collection.insert_one(log_entry)


def main():
  """Do nothing."""
  pass

if __name__ == '__main__':
  main()
