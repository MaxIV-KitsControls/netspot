#!/usr/bin/python -tt

"""Module to convert data in MongoDB to Ansible inventory JSON."""

# pylint: disable=C0103

import json
import os
import argparse

from netspot import NetSPOT, NetSPOTGroup

SPECIAL_FIELDS = ['_id', 'lastModified']

class Host(object):
  """Class to hold a host."""

  def __init__(self, device):
    self.hostname = device['asset']
    self.attributes = dict()

    # Add groups this deivce belongs
    self.groups = device['groups']

    for tag in device:
      # Break out user variables
      if tag == 'variables':
        for variable in device[tag]:
          for key in variable:
            self.add_attribute(key, variable[key])
      # Filter out MongoDB special tags
      elif tag not in SPECIAL_FIELDS:
        self.add_attribute(tag, device[tag])

  def add_attribute(self, attribute, value):
    """Add attribute to host."""
    self.attributes[attribute] = value

class Hostvars(object):
  """Class to hold host variables."""
  def __init__(self):
    self.hosts = dict()

  def add_host(self, host):
    """Add host and its attributes to the list of hosts."""
    self.hosts[host.hostname] = host.attributes

  def get_hostvars(self):
    """Returns Ansible formatted hostvars."""
    return {'hostvars': self.hosts}

class Group(object):
  """Class that hold group information."""

  def __init__(self, group):
    self.group = group
    self.members = list()
    self.vars = dict()

    # Get inventory
    inventory = NetSPOTGroup()

    # Add group variables
    group_vars = inventory.get_variables(group)
    for var in group_vars:
      if var.keys()[0] not in SPECIAL_FIELDS:
        self.add_vars(var.keys()[0], var.values()[0])

  def add_group_member(self, member):
    """Add group to list of groups."""
    self.members.append(member)

  def add_vars(self, var, value):
    """Add group vairables."""
    self.vars[var] = value

  def get_group(self):
    """Return Ansible formatted host and vars data."""
    return {'hosts': self.members,
            'vars': self.vars}

def AnsibleInventory(attribute=None, json_output=True):
  """Class to generate and return Ansible JSON inventory data."""

  # Get devices
  inventory = NetSPOT()

  if attribute:
    cursor = inventory.search(attribute)

  groups = dict()
  data = dict()
  hostvars = Hostvars()

  # Add devices
  for asset in cursor:
    # Create Host object and add it to hostvars
    host = Host(asset)
    hostvars.add_host(host)

    # Add group/role and group/role member
    for group in asset['groups']:
      if group not in groups:
        groups[group] = Group(group)

      # Add device as member to the group
      groups[group].add_group_member(asset['asset'])

      # Update group/role members in return data
      data.update({group: groups[group].get_group()})

    # Return data
    data.update({'_meta': hostvars.get_hostvars()})

  if json_output:
    return json.dumps(data, sort_keys=True, indent=4, separators=(',', ': '))
  else:
    return data

def main():
  """Print Ansible dynamic inventory."""
  # Arguments
  parser = argparse.ArgumentParser(description='MAX IV Network SPOT - netspot')
  parser.add_argument('-l', '--list', help='List all', action='store_true', required=True)
  parser.add_argument('-f', '--filter',
                      help='Filter: eg. group:blue',
                      action='store',
                      required=False,
                      default=None)
  args = parser.parse_args()

  if args.list:
    if args.filter:
      print AnsibleInventory(attribute=args.filter)
    elif os.environ.get('FILTER'):
      print AnsibleInventory(attribute=os.environ['FILTER'])
    else:
      print "Need filter criteria. Specify with -s or env variable FILTER."

if __name__ == '__main__':
  main()
