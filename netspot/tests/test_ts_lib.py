#!/usr/bin/python -tt
"""ts_lib tests

  Run: python -m unittest tests.test_ts_lib

"""

import unittest

import ts_lib


class TestTSLib(unittest.TestCase):
  def setUp(self):
    pass

  def test_Interface(self):
    cmd = 'show interfaces xe-0/1/0 detail'
    output = {cmd: """Physical interface: xe-0/1/0, Enabled, Physical link is Up
                      Interface index: 178, SNMP ifIndex: 600, Generation: 182
                      Description: Connected to w-netlab-sw-2:xe-0/0/40 [TESTTAG];
                      Link-level type: Ethernet, MTU: 1514, MRU: 0, Speed: 10Gbps, Duplex: Full-Duplex, BPDU Error: None, MAC-REWRITE Error: None,
                      Loopback: Disabled, Source filtering: Disabled, Flow control: Enabled
                      Device flags   : Present Running
                      Interface flags: SNMP-Traps Internal: 0x0
                      Link flags     : None
                      CoS queues     : 8 supported, 8 maximum usable queues
                      Hold-times     : Up 0 ms, Down 0 ms
                      Current address: 54:e0:32:30:87:33, Hardware address: 54:e0:32:30:87:33
                      Last flapped   : 2017-04-11 02:36:59 CEST (8w4d 03:05 ago)
                      Statistics last cleared: Never
                      Traffic statistics:
                       Input  bytes  :             62403995                    0 bps
                       Output bytes  :            307688484                    0 bps
                       Input  packets:               204502                    0 pps
                       Output packets:              3098567                    0 pps
                       IPv6 transit statistics:
                        Input  bytes  :                   0
                        Output bytes  :                   0
                        Input  packets:                   0
                        Output packets:                   0
                      Egress queues: 8 supported, 4 in use
                      Queue counters:       Queued packets  Transmitted packets      Dropped packets
                        0                                0               282440                    0
                        1                                0                    0                    0
                        5                                0                    0                    0
                        7                                0              4769919                    0
                      Queue number:         Mapped forwarding classes
                        0                   best-effort
                        1                   assured-forwarding
                        5                   expedited-forwarding
                        7                   network-control
                      Active alarms  : None
                      Active defects : None
                      Interface transmit statistics: Disabled

                      Logical interface xe-0/1/0.0 (Index 119) (SNMP ifIndex 601) (Generation 185)
                        Flags: Up SNMP-Traps 0x0 Encapsulation: ENET2
                        Traffic statistics:
                         Input  bytes  :             60469573
                         Output bytes  :            361077451
                         Input  packets:               187218
                         Output packets:              2919017
                        Local statistics:
                         Input  bytes  :             60469573
                         Output bytes  :            361077451
                         Input  packets:               187218
                         Output packets:              2919017
                        Transit statistics:
                         Input  bytes  :                    0                    0 bps
                         Output bytes  :                    0                    0 bps
                         Input  packets:                    0                    0 pps
                         Output packets:                    0                    0 pps
                        Protocol eth-switch, Generation: 205, Route table: 0
                          Flags: Trunk-Mode

                    {master:0}"""}

    show_interface = ts_lib.Interface(output[cmd])
    self.assertEqual('Up', show_interface.link_state)
    self.assertEqual('10Gbps', show_interface.speed)
    self.assertEqual('Full-Duplex', show_interface.duplex)
    self.assertEqual('2017-04-11 02:36:59 CEST (8w4d 03:05 ago)', show_interface.flapped)
    self.assertEqual('', show_interface.auto_neg)

  def test_LLDP(self):
    cmd = 'show lldp neighbors interface xe-0/1/0'
    output = {cmd: """LLDP Neighbor Information:
                      Local Information:
                      Index: 7 Time to live: 120 Time mark: Sat Jun 10 03:25:16 2017 Age: 11 secs 
                      Local Interface    : xe-0/1/0.0
                      Parent Interface   : -
                      Local Port ID      : 601
                      Ageout Count       : 0

                      Neighbour Information:
                      Chassis type       : Mac address
                      Chassis ID         : f8:c0:01:38:4f:38
                      Port type          : Locally assigned
                      Port ID            : 512
                      Port description   : xe-0/0/40
                      System name        : w-netlab-sw-2
                        
                      System Description : Juniper Networks, Inc. qfx3500s Ethernet Switch, kernel JUNOS 14.1X53-D30.3, Build date: 2015-10-02 12:06:45 UTC Copyright (c) 1996-2015 Juniper Networks, Inc.

                      System capabilities 
                              Supported  : Bridge Router 
                              Enabled    : Bridge Router 

                      Management Info 
                              Type              : IPv4
                              Address           : 192.168.96.151
                              Port ID           : 33
                              Subtype           : 1
                              Interface Subtype : ifIndex(2)
                              OID               : 1.3.6.1.2.1.31.1.1.1.1.33
                      Media endpoint class: Network Connectivity

                      Organization Info
                             OUI      : IEEE 802.3 Private (0x00120f)
                             Subtype  : MAC/PHY Configuration/Status (1)
                             Info     : Autonegotiation [not supported, not enabled (0x0)], PMD Autonegotiation Capability (0x8000), MAU Type (0x0)
                             Index    : 1

                      Organization Info
                             OUI      : IEEE 802.3 Private (0x00120f)
                             Subtype  : Link Aggregation (3)
                             Info     : Aggregation Status (supported ), Aggregation Port ID (0)
                             Index    : 2

                      Organization Info
                             OUI      : IEEE 802.3 Private (0x00120f)
                             Subtype  : Maximum Frame Size (4)
                             Info     : MTU Size (1514)
                             Index    : 3

                      Organization Info
                             OUI      : Juniper Specific (0x009069)
                             Subtype  : Chassis Serial Type (1)
                             Info     : Juniper Slot Serial [P5883-C]
                             Index    : 4

                      Organization Info
                             OUI      : Ethernet Bridged (0x0080c2)
                             Subtype  : VLAN Name (3)
                             Info     : VLAN ID (201), VLAN Name (vlan-201)
                             Index    : 5

                      Organization Info
                             OUI      : 0012bb
                             Subtype  : 1
                             Info     : 000F04 
                             Index    : 6
                      """}

    lldp_neighbors = ts_lib.LLDP(output[cmd])

    self.assertEqual('f8:c0:01:38:4f:38', lldp_neighbors.remote_chassis_id)
    self.assertEqual('xe-0/0/40', lldp_neighbors.remote_port_description)
    self.assertEqual('w-netlab-sw-2', lldp_neighbors.remote_system)

  def test_MACTable(self):
    cmd = 'show ethernet-switching table'
    output = {cmd: """Ethernet switching table : 4 entries, 4 learned
                      Routing instance : default-switch
                          Vlan                MAC                 MAC         Age    Logical
                          name                address             flags              interface
                          acc-3gev-dia        00:19:0f:0e:e2:06   D          1:22   ae0.0                
                          acc-3gev-dia        00:19:0f:12:76:3d   D             -   ae0.0                
                          acc-3gev-dia        00:e0:33:8d:68:39   D             -   ae0.0                
                          acc-3gev-dia        00:e0:33:ef:31:98   D             -   ae0.0                

                      MAC flags (S - static MAC, D - dynamic MAC, L - locally learned, P - Persistent static
                                 SE - statistics enabled, NM - non configured MAC, R - remote PE MAC)


                      Ethernet switching table : 5 entries, 5 learned
                      Routing instance : default-switch
                          Vlan                MAC                 MAC         Age    Logical
                          name                address             flags              interface
                          acc-ion-pump-ctrl-3gev 00:04:a3:38:e2:f2 D            -   ge-1/0/39.0                   
                          acc-ion-pump-ctrl-3gev 00:1e:c0:90:28:28 D            -   ge-4/0/32.0          
                          acc-ion-pump-ctrl-3gev 00:1e:c0:f6:a7:72 D            -   ge-1/0/44.0          
                          acc-ion-pump-ctrl-3gev 00:50:56:b3:7e:2c D            -   ae0.0                
                          acc-ion-pump-ctrl-3gev d8:80:39:e8:db:3a D            -   ge-1/0/45.0 

                      MAC flags (S - static MAC, D - dynamic MAC, L - locally learned, P - Persistent static
                                 SE - statistics enabled, NM - non configured MAC, R - remote PE MAC)


                      Ethernet switching table : 2 entries, 2 learned
                      Routing instance : default-switch
                          Vlan                MAC                 MAC         Age    Logical
                          name                address             flags              interface
                          acc-r3-mag-plc-06-10 00:02:04:08:0b:22  D             -   ae0.0                
                          acc-r3-mag-plc-06-10 00:02:04:08:0b:2b  D             -   ae0.0     
                          acc-r3-mag-plc-06-10 *                  D             -   ae0.0     
                      """}

    macs = ts_lib.MACTable(output[cmd])

    # Check number MACs returned
    self.assertEqual(11, len(macs.mac_entries))

    # Check entries
    self.assertEqual('1:22', macs.mac_entries[0]['age'])
    self.assertEqual('ae0.0', macs.mac_entries[0]['interface'])
    self.assertEqual('00:19:0f:0e:e2:06', macs.mac_entries[0]['mac'])
    self.assertEqual('D', macs.mac_entries[0]['type'])
    self.assertEqual('acc-3gev-dia', macs.mac_entries[0]['vlan'])

    self.assertEqual('-', macs.mac_entries[6]['age'])
    self.assertEqual('ge-1/0/44.0', macs.mac_entries[6]['interface'])
    self.assertEqual('00:1e:c0:f6:a7:72', macs.mac_entries[6]['mac'])
    self.assertEqual('D', macs.mac_entries[6]['type'])
    self.assertEqual('acc-ion-pump-ctrl-3gev', macs.mac_entries[6]['vlan'])
 
if __name__ == '__main__':
  unittest.main()
