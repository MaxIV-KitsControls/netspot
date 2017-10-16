#!/usr/bin/python -tt

""" NetCollector client."""

# pylint: disable=C0103

import argparse
import getpass
import net_collector
import netspot

from spotmax import SpotMAX

# Arguments
parser = argparse.ArgumentParser(description='NetSPOT Network Collector')
parser.add_argument('-a', '--asset', help='Asset', required=False)

# Username/password
parser.add_argument('-u', '--username', help='Username for device login', required=False)
parser.add_argument('-p', '--password', help='Password for device login', required=False)
parser.add_argument('-k', '--sshkey', help='Path to SSH key file', required=False)

args = parser.parse_args()

def ask_user_passwd():
  """Ask user for username and password.

  Returns:
    (username, password): tuple
  """

  if not args.username:
    username = raw_input('Username: ')
  else:
    username = args.username

  # Get password
  password = getpass.getpass()

  return (username, password)

class MACS(SpotMAX):
  """Class that interacts with the MongoDB backend."""

  def __init__(self, database=netspot.DATABASE, collection=netspot.COLL_MACS):
    SpotMAX.__init__(self, database, collection)

  def add_macs(self, device_macs):
    """Add MACs to database.

    Args:
      device_macs: dict, key: asset: asset name
                              macs: list of mac entries
    """

    # Add asset if it's a new asset
    if not self._exist(device_macs['asset'], key='asset'):
      # Add asset to database
      self.collection.insert_one(device_macs)
    else:
      # Update existing asset with the latest data
      update = {
          '$set': device_macs,
          '$currentDate': {'lastModified': True}
      }

      self.collection.update_one({'asset': device_macs['asset']}, update)


def main():
  """Main."""

  if args.asset:
    # Get username/password
    if not args.username or (not args.sshkey and not args.password):
      print 'Please specify device username/password.'
      username, password = ask_user_passwd()
    else:
      username = args.username
      password = args.password

    # Collect data from asset
    device = net_collector.NetCollector(args.asset, username, password, args.sshkey)

    # Add collected data to the database
    macs = MACS()
    macs.add_macs(device.device_macs)

    macs = net_collector.IPUsage(device.device_macs)
    macs.uppdate_ip()

  else:
    print 'Need more arguments. Please try -h'

if __name__ == '__main__':
  main()
