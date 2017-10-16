#!/usr/bin/python -tt

"""Helper functions."""

import re
import subprocess

from collections import defaultdict

from pymongo import MongoClient

from lib.spotmax import spotmax
from lib.spotmax import netspot
import netspot_settings



class BeamlineDenied(Exception):
  """Access denied to this beamline."""
  pass

def check_beamline_access(request, beamline):
  """Check if user have permission.

  Args:
    request: Django request object
    beamline: string, beamline

  Returns:
    True, if user have the correct permission

  Raises:
    BeamlineDenied
  """

  access = False

  # Staff users have access to all beamlines
  if request.user.is_staff:
    access = True
  # ALL group have access to all ports
  elif request.user.groups.filter(name='ALL').exists():
    access = True
  elif not request.user.groups.filter(name=beamline.upper()).exists():
    raise BeamlineDenied('You do not have access to this port/beamline - {0}'.format(beamline.upper()))
  else:
    access = True

  return access

def search_dhcp_log(search_term, dhcp_server='194.47.252.134'):
  """Search DHCP log files.

  Args:
    search_term: string, what to search for
    dhcp_server: string, IP address of the DHCP server

  Returns:
    dhcp_logs: list, list of lines from the DHCP logs
    dhcp_error: string, error message
  """

  dhcp_logs = []
  dhcp_error = None

  # Command to run
  command = '/bin/cat /var/log/syslog | grep {0}'.format(search_term)

  # SSH and run command
  ssh = subprocess.Popen(["ssh", "%s" % dhcp_server, command],
                         shell=False,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
  dhcp_logs = ssh.stdout.readlines()

  # Check for errors
  if dhcp_logs == []:
    dhcp_error = ssh.stderr.readlines()

  return dhcp_logs, dhcp_error

def get_dhcp_server(network=None, asset=[]):
  """Return IP address of DHCP server based on network or asset.

  Args:
    network: string, white, green or blue
    asset: string, asset name

  Return:
    dhcp_server: string, IP address
  """

  if network == 'blue' or asset[:1] == 'b':
    dhcp_server = '172.16.2.10'
  elif network == 'green' or asset[:1] == 'g':
    dhcp_server = '10.0.2.10'
  elif network == 'white' or asset[:1] == 'w':
    dhcp_server = '194.47.252.134'
  else:
    dhcp_server = None

  return dhcp_server

def mongo_helper(collection):
  """Helper function to connect to Mongo."""

  client = MongoClient()
  database = client[netspot_settings.DATABASE]
  database.authenticate(netspot_settings.DB_USERNAME, netspot_settings.DB_PASSWORD)
  collection = database[collection]

  return collection

def get_search_term(request):
  """Get search term from request.

  Args:
    request: Django request object

  Returns:
    searchterm: string, search term
  """

  # Get search term
  searchterm = request.POST.get('search', '')

  # If no POST data, try GET
  if not searchterm and request.GET.get('search', ''):
    searchterm = request.GET.get('search', '')

  return searchterm.strip()

def colorize_output(output):
  """Add HTML colors to the output."""

  # Task status
  color_output = re.sub(r'(ok: [-\w\d\[\]]+)',
                        r'<font color="green">\g<1></font>',
                        output)
  color_output = re.sub(r'(changed: [-\w\d\[\]]+)',
                        r'<font color="orange">\g<1></font>',
                        color_output)
  if not re.search(r'failed: 0', color_output):
    color_output = re.sub(r'(failed: [-\w\d\[\]]+)',
                          r'<font color="red">\g<1></font>',
                          color_output)

  color_output = re.sub(r'(fatal: [-\w\d\[\]]+):',
                        r'<font color="red">\g<1></font>',
                        color_output)
  # Play recap
  color_output = re.sub(r'(ok=[\d]+)',
                        r'<font color="green">\g<1></font>',
                        color_output)
  color_output = re.sub(r'(changed=[\d]+)',
                        r'<font color="orange">\g<1></font>',
                        color_output)


  color_output = re.sub(r'(failed=[1-9][0-9]*)',
                        r'<font color="red">\g<1></font>',
                        color_output)

  return color_output

def main():
  """Main."""
  pass

if __name__ == '__main__':
  main()
