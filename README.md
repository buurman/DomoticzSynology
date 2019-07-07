# DomoticzSynology
Synology SNMP Monitor on Domoticz

This plugin monitors the following services on Synology via SNMP service:
- NAS Status
- HDD Empty Space %
- NAS Temperature
- HDD Temperature up to 4 disks
- NAS CPU
- NAS Memory
- UPS Status
- UPS Charge %
- UPS Battery Time Left

* Thanks to @ycahome for SNMP Reader Plugin :  https://github.com/ycahome/SNMPreader

## Installation
1. On Synology: Open Control Panel - Terminal & SNMP - SNMP - Enable SNMP Service and SNMPv1,SNMPv2c service and note down Community password.
2. On Domoticz install pysnmp: pip3 install pysnmp
3. Install plugin.py to Domoticz plugins folder.

## Configuration
1. Address: Synology IP Address
2. Community: Synology SNMP Community Password
3. DSM OID: Change this OID to 38 on DSM 5.1, 41 on DSM 6.0, 42 on DSM 6.1, 51 on DSM 6.2
4. Check Interval: Poll interval in minutes
