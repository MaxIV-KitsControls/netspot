#!/usr/bin/python -tt

"""CLI client to interact with the NetSPOT database."""

# pylint: disable=C0103

import getpass
import argparse
from pprint import pprint

from netspot import Asset, NetSPOT, NetSPOTGroup

# Arguments
parser = argparse.ArgumentParser(description='MAX IV Network SPOT - netspot')
parser.add_argument('-s', '--search', help='Search for device|group', required=False)
parser.add_argument('-a', '--add', help='Add new device|group', required=False)
parser.add_argument('-d', '--delete', help='Delete asset', required=False)
parser.add_argument('-r', '--groups', help='Group name(s)', required=False)
parser.add_argument('-l', '--loopback', help='IPv4 loopback', required=False)
parser.add_argument('-y', '--discover', help='Trigger manual discovery process', required=False)

# Groups
parser.add_argument('-g', '--group', dest='group', action='store_true')
parser.add_argument('-z', '--addvar', help='Add group variable', nargs='*', required=False)
parser.add_argument('-x', '--delvar', help='Add group variable', nargs='*', required=False)

# Username/password and SSH key file
parser.add_argument('-u', '--username', help='Username for device login', required=False)
parser.add_argument('-p', '--password', help='Password for device login', required=False)
parser.add_argument('-k', '--sshkey', help='SSH Key file', required=False)

args = parser.parse_args()

def ask_user_passwd():
  """Ask user for username and password.

  Returns:
    username, password: tuple
  """

  if not args.username:
    username = raw_input('Username: ')
  else:
    username = args.username

  # Get password
  password = getpass.getpass()

  return username, password

def confirm_question(question):
  """Ask user for confirmation. Yes/No.

  Args:
    question: string, question eg. Delete X (Y/N).

  Returns:
    True/False: True if user answer y, ye or yes. False otherwise.

  """

  answer = raw_input(question)

  return answer.lower() in ['y', 'ye', 'yes']

def parse_asset():
  """Execute asset actions based on arguments."""

  # Get NetSPOT inventory
  inventory = NetSPOT()

  # Get username/password
  if not args.delete and not args.search:
    if not args.username or (not args.sshkey and not args.password):
      print 'Please specify device username/password.'
      username, password = ask_user_passwd()
    else:
      username = args.username
      password = args.password

  if args.add:
    if not args.loopback:
      print 'Loopback missing (specify with -l)'
    elif not args.groups:
      print 'Group missing - (specify with -g)'
    else:
      # Add new device
      asset = Asset(args.add, args.loopback, args.groups, username, password, args.sshkey)

      print 'Adding asset to database..'
      result = inventory.add_new_asset(asset)

      if result:
        print 'Asset added.'
      else:
        print 'Asset already exists.'

  elif args.delete:
    if confirm_question("Delete %s? (yes/no): " % args.delete):
      # Delete
      result = inventory.delete(args.delete, key='asset')

      if result:
        print '%s deleted.' % args.delete
      else:
        print 'Failed to delete or not found.'

    else:
      print "Nothing deleted."
  elif args.discover:
    asset = Asset(args.discover, username=username, password=password, ssh_keyfile=args.sshkey)

    # Discover asset
    print 'Gathering device facts.'
    result = inventory.discover(asset)

    if result:
      print 'Discover process succeeded.'
    else:
      print '%s does not exists.' % asset.asset

  elif args.search:
    # Search
    result = inventory.search(args.search, key='asset')

    # Present search result
    if result:
      for document in result:
        pprint(document)
      print '\nFound %s items.\n' % result.count()
    else:
      print 'Not found.'
  else:
    print 'Please specify an option. Try -h'

def parse_group():
  """Execute group actions based on arguments."""

  inventory = NetSPOTGroup()
  if args.add:
    # Add group
    result = inventory.add_group(args.add)

    if result:
      print 'Group added to database.'
    else:
      print 'Group already exists.'
  elif args.delete:
    # Delete group
    result = inventory.delete(args.delete, key='group')

    if result:
      print '%s deleted.' % args.delete
    else:
      print 'Failed to delete or not found.'
  elif args.search:
    # Search
    result = inventory.search(args.search, key='group')

    # Present search result
    if result:
      for document in result:
        pprint(document)
      print '\nFound %s items.\n' % len(result)
    else:
      print 'Not found.'
  elif args.addvar:
    if len(args.addvar) == 2:
      result = inventory.add_variable(target='group', name=args.addvar[0], variable=args.addvar[1])
      if result:
        print 'Update done.'
      else:
        print 'Group does not exist.'
    else:
      print 'Not enough parameters. Usage: -g -z GROUP_NAME VARIABLE:VALUE'
  elif args.delvar:
    if len(args.delvar) == 2:
      result = inventory.delete_variable(group=args.delvar[0], variable=args.delvar[1])
      if result:
        print 'Variable deleted.'
      else:
        print 'Group does not exist.'
    else:
      print 'Not enough parameters. Usage: -g -x GROUP_NAME VARIABLE'
  else:
    print 'Please specify an option. Try -h'

def main():
  """Perform action based on the arguments."""

  # Group
  if args.group:
    parse_group()
  # Asset
  else:
    parse_asset()

if __name__ == '__main__':
  main()
