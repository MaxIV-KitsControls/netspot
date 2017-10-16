#!/usr/bin/python -tt

"""Helper functions."""

from dns import resolver

# Exceptions
class CouldNotResolv(Exception):
  """Exception for unresolvable hostname."""
  pass

def resolv(hostname):
  """Select and query DNS servers.

  Args:
    hostname: string, hostname

  Returns:
    ips: list, list of IPs
  """

  ips = list()

  # Create resolver object
  res = resolver.Resolver()

  # Choose the correct DNS servers
  # Blue DNS servers
  if hostname.startswith('b-'):
    res.nameservers = ['172.16.2.10', '172.16.2.11']
  # Green DNS servers
  elif hostname.startswith('g-'):
    res.nameservers = ['10.0.2.10', '10.0.2.11']
  # Default to white DNS servers
  else:
    res.nameservers = ['194.47.252.134', '194.47.252.135']

  # Query
  try:
    query = res.query(hostname)
    for answer in query:
      ips.append(answer.address)
  except resolver.NXDOMAIN:
    raise CouldNotResolv

  # Return query result
  return ips

def main():
  """Main."""
  pass

if __name__ == '__main__':
  main()
