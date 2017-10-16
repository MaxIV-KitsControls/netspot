#
# netspot_settings_example.py: Copy this file to netspot_settings.py and fill in the blanks
#

import ldap
from django_auth_ldap.config import LDAPSearch, GroupOfNamesType

# MongoDB database and collections
DATABASE = 'netspot'                          # Database name
DB_USERNAME = ''                              # Database username
DB_PASSWORD = ''                              # Database password
COLL_NETSPOT = 'netspot'                      # Base collection
COLL_NETSPOT_GROUPS = 'netspot_groups'        # Groups collection name
COLL_MACS = 'netspot_macs'                    # MACs collection name
COLL_IP = 'netspot_ip_usage'                  # IP collection name
COLL_PLAYBOOK_LOGS = 'netspot_playbook_logs'  # Playbook log collection

# NetMagis database connection
NM_DATABASE = ''
NM_USERNAME = ''
NM_PASSWORD = ''
NM_SERVER = ''

# Playbooks
PLAYBOOK_PATH = ''                            # Path to where playbook files are stored
SLEEP_TIMER = 60                              # Time between checking the Ansible task queue
PORT_TEMPLATES = 'Network ports'              # Name of template category for port deployments/automation

# Task DB
TASK_DATABASE = ''                            # Path and name of the taskdb file eg. /blah/taskdb.db

# LDAP configuration
AUTH_LDAP_SERVER_URI = ''
AUTH_LDAP_START_TLS = True
AUTH_LDAP_GLOBAL_OPTIONS = {ldap.OPT_X_TLS_REQUIRE_CERT: ldap.OPT_X_TLS_NEVER}
AUTH_LDAP_BIND_DN = ''
AUTH_LDAP_BIND_PASSWORD = ''
AUTH_LDAP_USER_SEARCH = LDAPSearch('', ldap.SCOPE_SUBTREE, '')
AUTH_LDAP_CONNECTION_OPTIONS = {ldap.OPT_DEBUG_LEVEL: 0, ldap.OPT_REFERRALS: 0}

# Set up the basic group parameters.
AUTH_LDAP_GROUP_SEARCH = LDAPSearch('',ldap.SCOPE_SUBTREE, '')
AUTH_LDAP_GROUP_TYPE = GroupOfNamesType(name_attr='')
AUTH_LDAP_FIND_GROUP_PERMS = True
AUTH_LDAP_REQUIRE_GROUP = ''

# Cache group memberships for an hour to minimize LDAP traffic
AUTH_LDAP_CACHE_GROUPS = True
AUTH_LDAP_GROUP_CACHE_TIMEOUT = 3600