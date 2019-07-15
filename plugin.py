"""
<plugin key="SynoMonitor" name="Synology Monitor" author="febalci" version="1.0.2">
    <description>
        <h2>Synology Monitoring Plugin</h2><br/>
        Collects CPU, Memory, Heat and HDD Inormation from Synology NAS Units<br/>
        <br/>
        <h3>Installation:</h3><br/>
        pysnmp Python3 module should be installed first:<br/>
            pip3 install pysnmp<br/>
        <br/>
        <h3>Configuration:</h3><br/>
        On self.snmpHDTotal and self.snmpHDUsed Variables:<br/>
            Please Change DSM OID '51' to 38 on DSM 5.1, 41 on DSM 6.0, 42 on DSM 6.1, 51 on DSM 6.2
    </description>
    <params>
        <param field="Address" label="Synology IP Address" width="250px" required="true" default="192.168.1.1"/>
        <param field="Mode1" label="Community" width="250px" required="true" default="public"/>
        <param field="Mode2" label="DSM OID" width="200px" required="true" default="51"/>
        <param field="Mode4" label="Check Interval(min)" width="75px" required="true" default="1"/>
        <param field="Mode6" label="Debug" width="75px">
            <options>
                <option label="True" value="Debug"/>
                <option label="False" value="Normal"  default="true" />
            </options>
        </param>
    </params>
</plugin>
"""
import Domoticz
import sys
import site
for site in site.getsitepackages():
    sys.path.append(site)

from struct import unpack
from pysnmp.entity.rfc3413.oneliner import cmdgen
#v.1.0.2:   UPS Check Added, no UPS devices created if UPS missing
#           Added OL CHRG and OB DSCHRG for UPS
#           Added 5th HDD TEMP
#v.1.0.0:   First Commit

class BasePlugin:
    enabled = False

    def __init__(self):
        self.synoIP = ''
        self.synoCommunity = ''
        self.pollPeriod = 0
        self.pollCount = 0
        self.synoModel = ''
        self.snmpStatus = '.1.3.6.1.4.1.6574.1.1.0'
        self.snmpNASTemp = '1.3.6.1.4.1.6574.1.2.0'
        self.snmpTempHD1 = '1.3.6.1.4.1.6574.2.1.1.6.0'
        self.snmpTempHD2 = '1.3.6.1.4.1.6574.2.1.1.6.1'
        self.snmpTempHD3 = '1.3.6.1.4.1.6574.2.1.1.6.2'
        self.snmpTempHD4 = '1.3.6.1.4.1.6574.2.1.1.6.3'
        self.snmpTempHD5 = '1.3.6.1.4.1.6574.2.1.1.6.4' #v.1.0.1
        self.snmpStatusHD1 = '.1.3.6.1.4.1.6574.2.1.1.5.0'
        self.snmpStatusHD2 = '.1.3.6.1.4.1.6574.2.1.1.5.1'
        self.snmpStatusHD3 = '.1.3.6.1.4.1.6574.2.1.1.5.2'
        self.snmpStatusHD4 = '.1.3.6.1.4.1.6574.2.1.1.5.3'
        self.snmpStatusHD5 = '.1.3.6.1.4.1.6574.2.1.1.5.4' #v.1.0.1
        self.snmpHDTotal = '1.3.6.1.2.1.25.2.3.1.5.' # Change OID to .38 on DSM 5.1, .41 on DSM 6.0, 42 on DSM 6.1, 51 on DSM 6.2
        self.snmpHDUsed = '1.3.6.1.2.1.25.2.3.1.6.' # Change OID to .38 on DSM 5.1, .41 on DSM 6.0, 42 on DSM 6.1, 51 on DSM 6.2
        self.snmpCPUUser = '1.3.6.1.4.1.2021.11.9.0'
        self.snmpCPUSystem ='1.3.6.1.4.1.2021.11.10.0'
        self.snmpMemTotalSwap = '1.3.6.1.4.1.2021.4.3.0'
        self.snmpMemTotalReal = '1.3.6.1.4.1.2021.4.5.0'
        self.snmpMemTotalFree = '1.3.6.1.4.1.2021.4.11.0'
        self.snmpMemCached = '1.3.6.1.4.1.2021.4.15.0'
        self.snmpMemBuffer = '1.3.6.1.4.1.2021.4.14.0'
        self.snmpModel = '.1.3.6.1.4.1.6574.1.5.1.0'
        self.snmpUpsInfoStatus = '.1.3.6.1.4.1.6574.4.2.1.0'
        self.snmpUpsBatteryRuntime = '.1.3.6.1.4.1.6574.4.3.6.1.0'
        self.snmpUpsBatteryCharge = '.1.3.6.1.4.1.6574.4.3.1.1.0'
        self.ups = False
        return

    def onStart(self):
        Domoticz.Log("onStart called")
        if Parameters["Mode6"] == "Debug":
            Domoticz.Debugging(1)
            
#        if ("Synology" not in Images):
#            Domoticz.Image('SynoMonitor.zip').Create()
#            Domoticz.Debug('Icons Created...')
#        iconPID = Images["Life360Presence"].ID
        
        self.synoIP = Parameters["Address"]
        self.synoCommunity = Parameters["Mode1"]
        self.synoModel = str(getSNMPvalue(self.synoIP,self.snmpModel,self.synoCommunity))
        Domoticz.Debug ('Synology Model: '+self.synoModel)
        self.snmpHDTotal = self.snmpHDTotal + Parameters["Mode2"]
        self.snmpHDUsed = self.snmpHDUsed + Parameters["Mode2"]
        self.ups = str(getSNMPvalue(self.synoIP,self.snmpUpsBatteryCharge,self.synoCommunity))
        if self.ups[0:2] == '0x':
            self.ups = True
        else:
            self.ups = False


        if (len(Devices) == 0):
            Domoticz.Device(Name=self.synoModel+' Status', Unit=1, TypeName="Text", Used=1).Create()
            Domoticz.Device(Name=self.synoModel+' Temperature', Unit=2, TypeName="Temperature", Used=1).Create()
            Domoticz.Device(Name=self.synoModel+' HDD', Unit=3, TypeName="Percentage", Used=1).Create()
            Domoticz.Device(Name=self.synoModel+' HDD1 Temperature', Unit=4, TypeName="Temperature", Used=0).Create()
            Domoticz.Device(Name=self.synoModel+' HDD2 Temperature', Unit=5, TypeName="Temperature", Used=0).Create()
            Domoticz.Device(Name=self.synoModel+' HDD3 Temperature', Unit=6, TypeName="Temperature", Used=0).Create()
            Domoticz.Device(Name=self.synoModel+' HDD4 Temperature', Unit=7, TypeName="Temperature", Used=0).Create()
            Domoticz.Device(Name=self.synoModel+' HDD5 Temperature', Unit=13, TypeName="Temperature", Used=0).Create()
            Domoticz.Device(Name=self.synoModel+' CPU', Unit=8, TypeName="Percentage", Used=1).Create()
            Domoticz.Device(Name=self.synoModel+' Mem', Unit=9, TypeName="Percentage", Used=1).Create()
            if self.ups:
                Domoticz.Device(Name=self.synoModel+' UPS Status', Unit=10, TypeName="Text", Used=0).Create()
                Domoticz.Device(Name=self.synoModel+' UPS Charge', Unit=11, TypeName="Percentage", Used=0).Create()
                Domoticz.Device(Name=self.synoModel+' UPS Time', Unit=12, TypeName="Custom", Options={"Custom": "1;mins"}, Used=0).Create()

        self.pollPeriod = 6 * int(Parameters["Mode4"]) 
        self.pollCount = self.pollPeriod - 1
        Domoticz.Heartbeat(10)

    def onStop(self):
        Domoticz.Log("onStop called")

    def onConnect(self, Connection, Status, Description):
        Domoticz.Log("onConnect called")

    def onMessage(self, Connection, Data):
        Domoticz.Log("onMessage called")

    def onCommand(self, Unit, Command, Level, Hue):
        Domoticz.Log("onCommand called for Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level))

    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        Domoticz.Log("Notification: " + Name + "," + Subject + "," + Text + "," + Status + "," + str(Priority) + "," + Sound + "," + ImageFile)

    def onDisconnect(self, Connection):
        Domoticz.Log("onDisconnect called")

    def onHeartbeat(self):
        Domoticz.Debug("onHeartBeat called:"+str(self.pollCount)+"/"+str(self.pollPeriod))
        if self.pollCount >= self.pollPeriod:
            snmptemp, snmptemp2, snmptemp3 = '', '', ''
            #NAS Status
            snmptemp = str(getSNMPvalue(self.synoIP,self.snmpStatus,self.synoCommunity))
            if snmptemp == '1':
                snmptemp = 'Normal'
            elif snmptemp == '2':
                snmptemp = 'Failed!!!'
            else:
                snmptemp = 'Unknown'
            Domoticz.Debug('NAS Status: '+snmptemp)
            UpdateDevice(1,0,snmptemp)
            #NAS Temperature
            snmptemp = str(getSNMPvalue(self.synoIP,self.snmpNASTemp,self.synoCommunity))
            Domoticz.Debug('NAS Temperature: '+snmptemp)
            UpdateDevice(2,0,snmptemp)
            #NAS Memory
            memTotalSwap = getSNMPvalue(self.synoIP,self.snmpMemTotalSwap,self.synoCommunity)
            memTotalReal = getSNMPvalue(self.synoIP,self.snmpMemTotalReal,self.synoCommunity)
            memTotal = int(memTotalReal) + int(memTotalSwap)
            memCached = getSNMPvalue(self.synoIP,self.snmpMemCached,self.synoCommunity)
            memSwap = getSNMPvalue(self.synoIP,self.snmpMemBuffer,self.synoCommunity)
            memFree = getSNMPvalue(self.synoIP,self.snmpMemTotalFree,self.synoCommunity)
            memUsed = int(memCached) + int(memSwap) + int(memFree)
            memUtilization = ((memTotal - memUsed) / memTotal) * 100
            Domoticz.Debug('RAM Utilization: '+str(int(memUtilization,)))
            UpdateDevice(9,0,int(memUtilization))
            #NAS CPU
            snmptemp = getSNMPvalue(self.synoIP,self.snmpCPUUser,self.synoCommunity)
            snmptemp2 = getSNMPvalue(self.synoIP,self.snmpCPUSystem,self.synoCommunity)
            snmptemp3 = int(snmptemp) + int(snmptemp2)
            Domoticz.Debug('CPU: '+str(snmptemp3))
            UpdateDevice(8,0,snmptemp3)
            #NAS HDD Space
            hdUsed = getSNMPvalue(self.synoIP,self.snmpHDUsed,self.synoCommunity)
            Domoticz.Debug('HDD Used: '+hdUsed)
            hdTotal = getSNMPvalue(self.synoIP,self.snmpHDTotal,self.synoCommunity)
            Domoticz.Debug('HDD Total: '+hdTotal)
            try:
                snmptemp = (100*int(hdUsed))/int(hdTotal)
            except:
                snmptemp = "Wrong DSM OID!"
                Domoticz.Debug('HDD %: '+snmptemp)
                UpdateDevice(3,0,snmptemp)
            else:
                Domoticz.Debug('HDD %: '+str('%.2f' % snmptemp))
                UpdateDevice(3,0,'%.2f' % snmptemp)
            #NAS HDD1 Temperature
            snmptemp = str(getSNMPvalue(self.synoIP,self.snmpTempHD1,self.synoCommunity))
            Domoticz.Debug('HDD Temp 1: '+snmptemp)
            UpdateDevice(4,0,snmptemp)
            #NAS HDD2 Temperature
            snmptemp = str(getSNMPvalue(self.synoIP,self.snmpTempHD2,self.synoCommunity))
            Domoticz.Debug('HDD Temp 2: '+snmptemp)
            UpdateDevice(5,0,snmptemp)
            #NAS HDD3 Temperature
            snmptemp = str(getSNMPvalue(self.synoIP,self.snmpTempHD3,self.synoCommunity))
            Domoticz.Debug('HDD Temp 3: '+snmptemp)
            UpdateDevice(6,0,snmptemp)
            #NAS HDD4 Temperature
            snmptemp = str(getSNMPvalue(self.synoIP,self.snmpTempHD4,self.synoCommunity))
            Domoticz.Debug('HDD Temp 4: '+snmptemp)
            UpdateDevice(7,0,snmptemp)
            #NAS HDD5 Temperature
            snmptemp = str(getSNMPvalue(self.synoIP,self.snmpTempHD5,self.synoCommunity))
            Domoticz.Debug('HDD Temp 5: '+snmptemp)
            UpdateDevice(13,0,snmptemp)
            #UPS Status
            snmptemp = str(getSNMPvalue(self.synoIP,self.snmpUpsInfoStatus,self.synoCommunity))
            Domoticz.Debug('UPS Status: '+snmptemp)
            if snmptemp == 'OL':
                snmptemp = 'ONLINE'
            elif snmptemp == 'OB':
                snmptemp = 'ON BATTERY'
            elif snmptemp == 'LB':
                snmptemp = 'LOW BATTERY'
            elif snmptemp == 'HB':
                snmptemp = 'HIGH BATTERY'
            elif snmptemp == 'RB':
                snmptemp = 'REPLACE BATTERY'
            elif snmptemp == 'OL CHRG':
                snmptemp = 'ONLINE CHARGING'
            elif snmptemp == 'OB DISCHRG':
                snmptemp = 'ON BATTERY DISCHARGING'
            elif snmptemp == 'CHRG':
                snmptemp = 'CHARGING'
            elif snmptemp == 'DISCHRG':
                snmptemp = 'DISCHARGING'
            elif snmptemp == 'BYPASS':
                snmptemp = 'BYPASS'
            elif snmptemp == 'CAL':
                snmptemp = 'CALIBRATION'
            elif snmptemp == 'OFF':
                snmptemp = 'OFF'
            elif snmptemp == 'OVER':
                snmptemp = 'OVERLOAD'
            elif snmptemp == 'TRIM':
                snmptemp = 'SMART TRIM'
            elif snmptemp == 'BOOST':
                snmptemp = 'BOOST'
            elif snmptemp == 'FSD':
                snmptemp = 'FORCE SHUTDOWN'
            else:
                snmptemp = 'UNKNOWN'
            UpdateDevice(10,0,snmptemp)
            if self.ups:
                #UPS Charge
                snmptemp = str(getSNMPvalue(self.synoIP,self.snmpUpsBatteryCharge,self.synoCommunity))
                Domoticz.Debug('UPS Charge1: '+snmptemp)
                snmptemp = bytes.fromhex(snmptemp[2:])
                if snmptemp.startswith(b'\x9f\x78'):
                    snmptemp = unpack("!f", snmptemp[3:])[0]
                snmptemp = str(snmptemp)
                Domoticz.Debug('UPS Charge2: '+snmptemp)
    
                UpdateDevice(11,0,snmptemp)
                #UPS Time
                snmptemp = str(getSNMPvalue(self.synoIP,self.snmpUpsBatteryRuntime,self.synoCommunity))
                Domoticz.Debug('UPS Time: '+snmptemp)
                snmptemp = int(snmptemp)/60
                UpdateDevice(12,0,'%.0f' % snmptemp)

            self.pollCount = 0 #Reset Pollcount
        else:
            self.pollCount += 1

global _plugin
_plugin = BasePlugin()

def onStart():
    global _plugin
    _plugin.onStart()

def onStop():
    global _plugin
    _plugin.onStop()

def onConnect(Connection, Status, Description):
    global _plugin
    _plugin.onConnect(Connection, Status, Description)

def onMessage(Connection, Data):
    global _plugin
    _plugin.onMessage(Connection, Data)

def onCommand(Unit, Command, Level, Hue):
    global _plugin
    _plugin.onCommand(Unit, Command, Level, Hue)

def onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile):
    global _plugin
    _plugin.onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile)

def onDisconnect(Connection):
    global _plugin
    _plugin.onDisconnect(Connection)

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()

    # Generic helper functions
def UpdateDevice(Unit, nValue, sValue):
    # Make sure that the Domoticz device still exists (they can be deleted) before updating it 
    if (Unit in Devices):
        if (Devices[Unit].nValue != nValue) or (Devices[Unit].sValue != sValue):
            Devices[Unit].Update(nValue=nValue, sValue=str(sValue))
            Domoticz.Debug("Update "+str(nValue)+":'"+str(sValue)+"' ("+Devices[Unit].Name+")")
    return

def DumpConfigToLog():
    for x in Parameters:
        if Parameters[x] != "":
            Domoticz.Debug( "'" + x + "':'" + str(Parameters[x]) + "'")
    Domoticz.Debug("Device count: " + str(len(Devices)))
    for x in Devices:
        Domoticz.Debug("Device:           " + str(x) + " - " + str(Devices[x]))
        Domoticz.Debug("Device ID:       '" + str(Devices[x].ID) + "'")
        Domoticz.Debug("Device Name:     '" + Devices[x].Name + "'")
        Domoticz.Debug("Device nValue:    " + str(Devices[x].nValue))
        Domoticz.Debug("Device sValue:   '" + Devices[x].sValue + "'")
        Domoticz.Debug("Device LastLevel: " + str(Devices[x].LastLevel))
    return

# pysnmp helper functions
def getSNMPvalue(ServerIP,snmpOID,snmpCommunity):

    cmdGen = cmdgen.CommandGenerator()

    genData = cmdgen.CommunityData(str(snmpCommunity))
#    Domoticz.Debug("genData Loaded." + str(genData))

    TTData = cmdgen.UdpTransportTarget((str(ServerIP), 161), retries=2)
#    Domoticz.Debug("TTData Loaded." + str(TTData))

    errorIndication, errorStatus, errorIndex, varBinds = cmdGen.getCmd(genData,TTData,snmpOID)
#    Domoticz.Debug("DATA Loaded." + str(varBinds))

    # Check for errors and print out results
    if errorIndication:
        Domoticz.Error(str(errorIndication))
    else:
        if errorStatus:
            Domoticz.Error('%s at %s' % (errorStatus.prettyPrint(),errorIndex and varBinds[int(errorIndex)-1] or '?'))
        else:
            for name, val in varBinds:
#                Domoticz.Debug('%s = %s' % (name.prettyPrint(), val.prettyPrint()))

                return val.prettyPrint()
    return