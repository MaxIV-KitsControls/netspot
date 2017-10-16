#!/usr/bin/python -tt

"""Run Ansible."""

# pylint: disable=W0212
# pylint: disable=R0902
# pylint: disable=R0913
# pylint: disable=R0914

from ansible.inventory import Inventory
from ansible.vars import VariableManager
from ansible.parsing.dataloader import DataLoader
from ansible.executor import playbook_executor
from ansible.utils.display import Display
from ansible.errors import AnsibleError

class Options(object):
  """Options class to replace Ansible OptParser."""

  def __init__(self, verbosity=None, inventory=None, listhosts=None, subset=None, module_paths=None,
               extra_vars=None, forks=None, ask_vault_pass=None, vault_password_files=None,
               new_vault_password_file=None, output_file=None, tags=None, skip_tags=None,
               one_line=None, tree=None, ask_sudo_pass=None, ask_su_pass=None, sudo=None,
               sudo_user=None, become=None, become_method=None, become_user=None,
               become_ask_pass=None, ask_pass=None, private_key_file=None, remote_user=None,
               connection=None, timeout=150, ssh_common_args=None, sftp_extra_args=None,
               scp_extra_args=None, ssh_extra_args=None, poll_interval=None, seconds=None,
               check=None, syntax=None, diff=None, force_handlers=None, flush_cache=None,
               listtasks=None, listtags=None, module_path=None):

    self.verbosity = verbosity
    self.inventory = inventory
    self.listhosts = listhosts
    self.subset = subset
    self.module_paths = module_paths
    self.extra_vars = extra_vars
    self.forks = forks
    self.ask_vault_pass = ask_vault_pass
    self.vault_password_files = vault_password_files
    self.new_vault_password_file = new_vault_password_file
    self.output_file = output_file

    # Tags
    if tags:
      self.tags = tags
    else:
      self.tags = []

    if skip_tags:
      self.skip_tags = skip_tags
    else:
      self.skip_tags = []

    self.one_line = one_line
    self.tree = tree
    self.ask_sudo_pass = ask_sudo_pass
    self.ask_su_pass = ask_su_pass
    self.sudo = sudo
    self.sudo_user = sudo_user
    self.become = become
    self.become_method = become_method
    self.become_user = become_user
    self.become_ask_pass = become_ask_pass
    self.ask_pass = ask_pass
    self.private_key_file = private_key_file
    self.remote_user = remote_user
    self.connection = connection
    self.timeout = timeout
    self.ssh_common_args = ssh_common_args
    self.sftp_extra_args = sftp_extra_args
    self.scp_extra_args = scp_extra_args
    self.ssh_extra_args = ssh_extra_args
    self.poll_interval = poll_interval
    self.seconds = seconds
    self.check = check
    self.syntax = syntax
    self.diff = diff
    self.force_handlers = force_handlers
    self.flush_cache = flush_cache
    self.listtasks = listtasks
    self.listtags = listtags
    self.module_path = module_path

class Host(object):
  """Helper class."""
  def __init__(self, host):
    self.host = host

  def get_name(self):
    """Return hostname."""

    return self.host

class Runner(object):
  """Ansible Playbook runner."""

  def __init__(self,
               username,
               playbook,
               private_key_file,
               inventory_data,
               extra_vars,
               become_pass,
               verbosity=0,
               search_filter=None):
    """
    Args:
      username: string, username of user running the playbook
      playbook: string, full playbook path eg. /tmp/my_pb.yml
      private_key_file: string, private key file
      inventory_data: dict, inventory data
      extra_vars: dict, Ansible extra vars, key = variable name
      become_pass: string, become password
      verbosity: integer, verbosity level
      search_filter: string, hosts/groups to match
    """

    self.playbook = playbook
    self.username = username
    self.inventory_data = inventory_data
    self.extra_vars = extra_vars
    self.search_filter = search_filter

    self.options = Options()
    self.options.private_key_file = private_key_file
    self.options.verbosity = verbosity
    self.options.connection = 'ssh'  # Need a connection type "smart" or "ssh"
    self.options.become = True
    self.options.become_method = 'sudo'
    self.options.become_user = 'automation'

    # Set global verbosity
    self.display = Display()
    self.display.verbosity = self.options.verbosity
    # Executor appears to have it's own verbosity object/setting as well
    playbook_executor.verbosity = self.options.verbosity

    # Become Pass Needed if not logging in as user root
    passwords = {'become_pass': become_pass}

    # Gets data from YAML/JSON files
    self.loader = DataLoader()

    # ORIGNAL on line 1
    #self.loader.set_vault_password(os.environ['VAULT_PASS'])
    self.loader.set_vault_password('secret')

    # All the variables from all the various places
    self.variable_manager = VariableManager()

    # Set of hosts
    hosts = set()

    # Load group variable
    for group in self.inventory_data:
      if group != '_meta':
        for host in self.inventory_data[group]['hosts']:
          host_obj = Host(host)
          hosts.add(host)
          for var in self.inventory_data[group]['vars']:
            self.variable_manager.set_host_variable(host_obj,
                                                    var,
                                                    self.inventory_data[group]['vars'][var])

    # Load host variables
    for host in self.inventory_data['_meta']['hostvars']:
      for var in self.inventory_data['_meta']['hostvars'][host]:
        host_obj = Host(host)
        self.variable_manager.set_host_variable(host_obj,
                                                var,
                                                self.inventory_data['_meta']['hostvars'][host][var])

    self.variable_manager.extra_vars = self.extra_vars

    # Set inventory, using most of above objects
    self.inventory = Inventory(loader=self.loader,
                               variable_manager=self.variable_manager,
                               host_list=list(hosts))
    self.variable_manager.set_inventory(self.inventory)

    # Setup playbook executor, but don't run until run() called
    self.pbex = playbook_executor.PlaybookExecutor(
        playbooks=[self.playbook],
        inventory=self.inventory,
        variable_manager=self.variable_manager,
        loader=self.loader,
        options=self.options,
        passwords=passwords)

  def run(self):
    """Run playbook."""

    # Results of PlaybookExecutor
    stats = None
    play_recap = {}

    try:
      self.pbex.run()
      stats = self.pbex._tqm._stats
    except AnsibleError as error:
      print 'Error', error
      self.pbex._tqm.send_callback('record_logs',
                                   username=self.username,
                                   success=False,
                                   extra_vars=self.extra_vars,
                                   playbook=self.playbook,
                                   search_filter=self.search_filter)
      raise AnsibleError
    finally:
      if stats:
        self.pbex._tqm.cleanup()

        # Test if success for record_logs
        run_success = True
        hosts = sorted(stats.processed.keys())
        for host in hosts:
          play_recap = stats.summarize(host)
          if play_recap['unreachable'] > 0 or play_recap['failures'] > 0:
            run_success = False

    # Dirty hack to send callback to save logs with data we want
    # Note that function "record_logs" is one I created and put into
    # the playbook callback file
    self.pbex._tqm.send_callback('record_logs',
                                 username=self.username,
                                 success=run_success,
                                 extra_vars=self.extra_vars,
                                 playbook=self.playbook,
                                 search_filter=self.search_filter)

    return play_recap
