#!/usr/bin/python -tt

"""NetMagis DB helper."""

import psycopg2
import netspot_settings

class NetMagisDB(object):
  """NetMagis DB helper class."""

  def __init__(self):
    """Init."""

    self.database = netspot_settings.NM_DATABASE
    self.username = netspot_settings.NM_USERNAME
    self.password = netspot_settings.NM_PASSWORD
    self.db_server = netspot_settings.NM_SERVER
    self.cursor = None
    self.conn = None

  def query(self, sql):
    """Query database.

    Args:
      sql: string, SQL query

    Returns:
      SQL result dict
    """

    self.cursor.execute(sql)

    return self.cursor.fetchall()

  def __enter__(self):
    """Enter."""

    # Open connection to DB server
    self.conn = psycopg2.connect(dbname=self.database,
                                 user=self.username,
                                 host=self.db_server,
                                 password=self.password)
    # Create cursor
    self.cursor = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    return self

  def __exit__(self, ex_type, ex_value, traceback):
    """Exit."""

    self.conn.close()

  def search(self, search):
    """Search function for NetMagis.

    Args:
      search: string, search key word

    Returns:
      NetMagis serach result, list

    """

    if search:
      sql = """SELECT * FROM dns.rr_ip
           RIGHT JOIN dns.rr
             ON dns.rr_ip.idrr=dns.rr.idrr
           WHERE dns.rr.name LIKE '%{0}%' OR
                 TEXT(dns.rr_ip.addr) LIKE '%{0}%' OR
                 TEXT(dns.rr.mac) LIKE LOWER('%{0}%');""".format(search)
      result = self.query(sql)
    else:
      result = []

    return result

  def get_arecord(self, iddr):
    """Find DNS A records from a NetMagis IDDR.

    Args:
      iddr: string, NetMagis IDDR

    Returns:
      arecord: SQL record with A record.
    """

    sql = """SELECT * FROM dns.rr
         RIGHT JOIN dns.rr_cname
           ON dns.rr.idrr=dns.rr_cname.cname
         RIGHT JOIN dns.rr_ip
           ON dns.rr_ip.idrr=dns.rr.idrr
         WHERE dns.rr_cname.idrr = '{0}';""".format(iddr)

    return self.query(sql)

def main():
  """Main."""
  pass

if __name__ == '__main__':
  main()
