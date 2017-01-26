#! /usr/bin/env python
# -*- coding: utf-8 -*-
####################
# Copyright (c) 2013, Richard Perlman All rights reserved.
# with much credit to Rob Smith (kormoc) -- https://github.com/BrightcoveOS/Diamond/blob/master/src/collectors/apcupsd/apcupsd.py
#

################################################################################
# Imports
################################################################################
from berkinet import logger
from ghpu import GitHubPluginUpdater
import inspect
import os
import socket
import string
import sys
import threading 
import urllib
import indigo
import time

################################################################################
# Globals
################################################################################

def eventServer(self, host, port): 
    funcName = inspect.stack()[0][3]
    dbFlg = False
    self.log.log(2, dbFlg, "%s called" % (funcName), self.logName)
    self.log.log(3, dbFlg, "%s: received address: %s and port: %s" % (funcName, host, port), self.logName)

    size = 24 
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
    server.bind((host, port)) 
    server.listen(5) 

    self.log.log(2, dbFlg, "%s: started listening on %s" % (funcName, server.getsockname()), self.logName)

    while self.serverRun: 
        try:
            self.log.log(4, dbFlg, "%s: waiting for a connection" % (funcName), self.logName)
            client, client_address = server.accept()

            self.log.log(3, dbFlg, "%s: client connected from, address: %s port: %s" % (funcName, client_address[0], client_address[1]), self.logName)

            if client_address[0] in self.useIpConnAccess: 
                data = client.recv(size)
                if  data:
                    self.log.log(3, dbFlg, "%s: received %s" % (funcName, data), self.logName)
                    self.buildAction(data)
                client.close()
            else:
                self.log.logError("%s: unauthorized client attempted access from: address: %s port: %s" % (funcName, client_address[0], client_address[1]), self.logName)

        except socket.timeout:
                pass

        except Exception, e:
                e1 = sys.exc_info()[0]
                self.log.logError("%s: read loop: Errors %s & %s" % (funcName, e, e1), self.logName)
                pass

        self.sleep(1)

    client.close()
    self.log.log(2, dbFlg, "%s server closed" % (funcName), self.logName)

########################################
def find_in_path(self, file_name, def_path=os.defpath):
        funcName = inspect.stack()[0][3]
        dbFlg = False
        path = os.getenv('PATH', def_path)
        self.log.log(2, dbFlg, "%s: PATH to search: %s" % (funcName, path), self.logName)
        for d in path.split(os.pathsep):
                file_path = os.path.abspath(os.path.join(d, file_name))
                if os.path.exists(file_path):
                        self.log.log(2, dbFlg, "%s: found %s" % (funcName, file_path), self.logName)
                        return file_path
        self.log.log(2, dbFlg, "%s: %s not found in PATH" % (funcName, file_name), self.logName)
        return file_name

################################################################################
         # delayAmount : 900
            # description : plugin action
            # * deviceId : 145579207
            # pluginId : com.berkinet.apcupsd
            # * pluginTypeId : apcupsdServerEvent
            # * props : com.berkinet.apcupsd : (dict)
            #      actionType : commok (string)
            # replaceExisting : True
            # textToSpeak : 

class Action(object):
    def __init__(self):
        self.description = 'plugin generated action'
        self.deviceId = 0
        self.pluginId = 'com.berkinet.apcupsd'
        self.pluginTypeId = None
        self.props = {'actionType': None}
    def __str__(self):
        desc_str = "description: %s\ndeviceId: %s \npluginId: %s \npluginTypeId: %s \n     props: %s \n" %(self.description, self.deviceId, self.pluginId, self.pluginTypeId, self.props)
        return desc_str


################################################################################
################################################################################
class Plugin(indigo.PluginBase):
    ########################################
    # Class properties
    ########################################
    def __init__(self, pluginid, pluginDisplayName, pluginVersion, pluginPrefs):
        indigo.PluginBase.__init__(self, pluginid, pluginDisplayName, pluginVersion, pluginPrefs)

        self.log = logger(self)
        self.logName = pluginDisplayName
        funcName = inspect.stack()[0][3]
        dbFlg = False
        self.log.log(2, dbFlg, "%s called" % (funcName), self.logName)

        try:
            self.apcupsdTimeout = string.atof(self.pluginPrefs["apcupsdTimeout"])
        except:
            self.apcupsdTimeout = 8
            self.log.logError("The apcupsd plugin appears to have not been configured. Default values will be used until the configuration is changed.", self.logName)

        self.apcupsdFrequency = string.atof(self.pluginPrefs.get("apcupsdFrequency", 5))
        self.useIpConn = self.pluginPrefs.get("useIpConn", False)
        if self.useIpConn:
            self.useIpConnAccess = self.pluginPrefs.get("useIpConnAccess", '127.0.0.1').split(', ')
            self.log.log(2, dbFlg, "%s: read access list: %s" % (funcName, self.useIpConnAccess), self.logName)

        self.pluginid = pluginid
        self.pluginDisplayName = pluginDisplayName
        self.apcupsdCommError = False
        self.triggerList = []
        self.triggerDict = {}
        self.defaultStatesDict = eval(open("../Resources/defaultStates.dict").read())
        self.commLostStatesList = eval(open("../Resources/commLostStates.List").read())
        self.serverRun = True
        self.readLoop = True
        self.startingUp = True

	# setup the plugin update checker... it will be disabled if the URL is empty
	self.updater = GitHubPluginUpdater(self)
	daysBetweenUpdateChecks = string.atof(self.pluginPrefs.get("daysBetweenUpdateChecks", 1))
	self.secondsBetweenUpdateChecks = daysBetweenUpdateChecks * 86400
	self.nextUpdateCheck = 0	# this will force an update check as soon as the plugin is running

	binary = "apcaccess"
	self.utility_binary = find_in_path(self, binary, "/usr/local/sbin:/sbin")
	self.utility_binary_found = True
	if binary == self.utility_binary:
		self.utility_binary_found = False
		self.log.logError("Could not find the '%s' binary. Is the APCUPSD package installed?" % (binary), self.logName)

	self.removeUnits = self.pluginPrefs.get("removeUnits", True)

        self.log.log(2, dbFlg, "%s: Completed" % (funcName), self.logName)

    ########################################
    def __del__(self):
        indigo.PluginBase.__del__(self)

    ########################################
    def startup(self): 
        funcName = inspect.stack()[0][3]
        dbFlg = False
        self.log.log(1, dbFlg, "%s: Plugin Starting" % (funcName), self.logName)

        self.log.log(2, dbFlg, "%s: completed" % (funcName), self.logName)

    ########################################
    def closedPrefsConfigUi (self, valuesDict, UserCancelled):
        funcName = inspect.stack()[0][3]
        dbFlg = False
        self.log.log(2, dbFlg, "%s called" % (funcName), self.logName)
        self.log.log(2, dbFlg, "%s:\nvaluesDict:\n%s\nUserCancelled: %s" % (funcName, valuesDict, UserCancelled), self.logName)

        if UserCancelled is False:
            self.log = logger(self)
            self.apcupsdTimeout = string.atof(valuesDict["apcupsdTimeout"])
            socket.setdefaulttimeout(self.apcupsdTimeout)
            self.apcupsdFrequency = string.atof(valuesDict["apcupsdFrequency"])
            self.useIpConn = valuesDict["useIpConn"]
            if self.useIpConn:
                self.useIpConnAccess = valuesDict["useIpConnAccess"].split(', ')
                self.log.log(2, dbFlg, "%s: read access list: %s" % (funcName, self.useIpConnAccess), self.logName)
            daysBetweenUpdateChecks = string.atoi(valuesDict["daysBetweenUpdateChecks"])
            self.secondsBetweenUpdateChecks = daysBetweenUpdateChecks * 86400
            self.nextUpdateCheck = 0        # this will force an update check starting now

            self.log.log(1, dbFlg, "Plugin options reset. Polling apcupsd servers every %s minutes with a %s second timeout and a debug level of %i" % (self.apcupsdFrequency, int(self.apcupsdTimeout), int(valuesDict["showDebugInfo1"])), self.logName)   
        self.log.log(3, dbFlg, "%s: Completed" % (funcName), self.logName)

    ########################################
    # this is also called by the custom menu item
    ########################################
    def checkForUpdates(self):
        update = self.updater.getLatestRelease()
        if update == None:
                self.log.logError("Error encountered checking for a new plugin version", self.logName)
        else:
                update = self.updater.checkForUpdate()

    ########################################
    def runConcurrentThread(self):
        funcName = inspect.stack()[0][3]
        dbFlg = False
        self.log.log(2, dbFlg, "%s called" % (funcName), self.logName)

        self.startingUp = False
	if self.utility_binary_found is False:
            self.log.logError("Plugin being shutdown pending installation of the APCUPSD package", self.logName)
	    self.stopPlugin()
	    self.sleep(10) # give it a few seconds for the stopPlugin to take effect, othewise this thread continues

        if self.useIpConn:
            port = int(self.pluginPrefs["useIpConnPort"])
            self.s = threading.Thread(target=eventServer, args=[self, '0.0.0.0', port])
            self.s.daemon = True
            self.s.start()
            self.log.log(1, dbFlg, "Event comms server started", self.logName)

        socket.setdefaulttimeout(self.apcupsdTimeout)

        if self.secondsBetweenUpdateChecks > 0:
                # obtain the current date/time and determine if it is after the previously-calculated
                # next check run
                timeNow = time.time()
                if timeNow > self.nextUpdateCheck:
                        self.pluginPrefs[u'updaterLastCheck'] = timeNow
                        self.log.log(3, dbFlg, "# of seconds between update checks: %s" % (int(self.secondsBetweenUpdateChecks)), self.logName)
                        self.nextUpdateCheck = timeNow + self.secondsBetweenUpdateChecks
                        # use the updater to check for an update now
                        self.checkForUpdates()

        try:
            self.log.log(1, dbFlg, "Plugin started. Polling apcupsd server(s) every %s minutes with a timeout of %s seconds" %  (self.apcupsdFrequency, int(self.apcupsdTimeout)), self.logName)
        except:
            self.log.logError("Plugin start delayed pending completion of initial plugin configuration", self.logName)
            return

        try:
            while True:
                self.readLoop = True
                prId = "com.berkinet.apcupsd"
                devCount = 0
                for dev in indigo.devices.iter(prId):    
                    if dev.enabled:
                        devCount += 1
                        self.log.log(2, dbFlg, "%s: Got device %s from Indigo" % (funcName, dev.name), self.logName)
                        self.readApcupsd(dev)
                        self.log.log(3, dbFlg, "%s: Read device %s" % (funcName, dev.name), self.logName)

                if devCount == 0 and self.logLevel > 0:
                    self.log.log(2, dbFlg, "%s: Completed device poll. No enabled devices found" % (funcName), self.logName)
                else:
                    if devCount == 1:
                        devWord = "device"
                    else:
                        devWord = "devices"
                    self.log.log(2, dbFlg, "%s: Completed device poll. %s %s found" % (funcName, devCount, devWord), self.logName)
                
                # we sleep (apcupsdFrequency minutes) between reads - in 1 sec increments so we can be interupted
                count = 0
                while count < self.apcupsdFrequency * 60 and self.readLoop:
                    self.sleep(1)
                    count +=1

        except self.StopThread:
            self.log.log(2, dbFlg, "%s: StopThread is now True" % (funcName), self.logName)
            self.serverRun = False
            self.sleep(1)

        self.log.log(3, dbFlg, "%s: Completed" % (funcName), self.logName)

    ########################################
    def readApcupsd(self, dev):
        funcName = inspect.stack()[0][3]
        dbFlg = False
        self.log.log(2, dbFlg, "%s called" % (funcName), self.logName)
        self.log.log(4, dbFlg, "%s: Received device:%s" % (funcName, dev), self.logName)

        sAddress = dev.pluginProps["apcupsdAddress"]
        sPort = dev.pluginProps["apcupsdPort"]
        self.log.log(4, dbFlg, "%s: doing apcaccess status for address %s on port %s" % (funcName, sAddress, sPort), self.logName)

        apcupsdSuccess = False
        apcupsdRetries = 0

        while not apcupsdSuccess and apcupsdRetries < 5:
            if apcupsdRetries == 0:
                self.log.log(3, dbFlg, "%s: starting read. Retries=%s" % (funcName, apcupsdRetries), self.logName)
            else:
                self.log.log(2, dbFlg, "%s: starting read. Retries=%s" % (funcName, apcupsdRetries), self.logName)

            apcupsdRetries = apcupsdRetries + 1

            report = os.popen(self.utility_binary + " status " + sAddress + " " + sPort).read()
            result = os.popen(self.utility_binary + " status " + sAddress + " " + sPort).close()
            if result:
                self.log.logError("%s: Connection to apcaccess failed with error code %s. Attempt %s of 5" % (funcName, result, apcupsdRetries), self.logName)
                apcupsdSuccess = False
                self.sleep(1)
            else:
                self.log.log(4, dbFlg, "%s: report\n%s" % (funcName, report), self.logName)

                result, apcupsdRetries
     
                metrics = {}

                for line in report.split('\n'):
                    (key,spl,val) = line.partition(': ')
                    key = key.rstrip().lower()
                    val = val.strip()
                    if self.removeUnits is True:
                        test = val.split()
                        if len(test) >= 2:
                            unit = test[1] # is there a "units" keyword here?
                            if unit == 'Seconds' or unit == 'Minutes' or unit == 'Hours' or unit == 'Watts' or unit == 'Volts' or unit == 'Percent':
                                val = test[0] # ignore anything after 1st space
                    if key != '':
                        metrics[key] = val
                        self.log.log(4, dbFlg, "%s: parsed key=%s and val=%s" % (funcName, key, val), self.logName)

                if 'status' in metrics:
                    apcupsdSuccess = True

                    if metrics['status'] == 'COMMLOST' and not self.apcupsdCommError:
                        dev.setErrorStateOnServer(u'lost comm')
                        self.apcupsdCommError = True
                        for state in dev.states:
                            try:
                                    dev.updateStateOnServer(key=state, value='n/a', clearErrorState=False)
                            except:
                                    dev.updateStateOnServer(key=state, value='n/a')
                            self.log.log(2, dbFlg, "%s: changing state for: %s to n/a" % (funcName, state), self.logName)
                        
                        self.log.log(3, dbFlg, "%s: COMMLOST" % (funcName), self.logName)
                    elif metrics['status'] != 'COMMLOST' and self.apcupsdCommError:
                        dev.setErrorStateOnServer(None)
                        self.apcupsdCommError = False
                        self.log.log(3, dbFlg, "%s: ONLINE" % (funcName), self.logName)

        if apcupsdSuccess:
            for metric in metrics: 
                value = metrics[metric]
                try:
                    if metric in dev.states:
                        self.log.log(3, dbFlg, "%s: found metric: %s " % (funcName, metric), self.logName)

                        if self.apcupsdCommError:
                            if metric in self.commLostStatesList:
                                self.log.log(3, dbFlg, "%s: found commLostStates: %s in list:%s" % (funcName, metric, self.commLostStatesList), self.logName)
                                try:
                                        dev.updateStateOnServer(key=metric, value=value + ' *', clearErrorState=False)
                                except:
                                        dev.updateStateOnServer(key=metric, value=value + ' *')
                            else:
                                pass
                        else:
                            try:
                                    dev.updateStateOnServer(key=metric, value=value, clearErrorState=False)
                            except:
                                    dev.updateStateOnServer(key=metric, value=value)
                        
                        self.log.log(3, dbFlg, "%s: metric:%s, val:%s, is Error:%s" % (funcName, metric, value, self.apcupsdCommError), self.logName)
                except:
                    self.log.logError("%s: error writing device state" % (funcName), self.logName)

            self.log.log(2, dbFlg, "%s:  Completed readings update from device: %s" % (funcName, dev.name), self.logName)
        else:
            self.log.logError("%s: Failed to get status for UPS %s after %s tries. Will retry in %s minutes" % (funcName, dev.name, apcupsdRetries, self.apcupsdFrequency), self.logName)

    ########################################
    # Device start, stop, modify and delete
    ########################################
    def deviceStartComm(self, dev):
        funcName = inspect.stack()[0][3]
        dbFlg = False
        self.log.log(2, dbFlg, "%s called for devce %s" % (funcName, dev.name), self.logName)

        if dev.enabled and not self.startingUp:
            self.log.log(2, dbFlg, "%s: Resetting read loop to include device %s" % (funcName, dev.name), self.logName)
            self.readLoop = False

        self.log.log(2, dbFlg, "%s: Completed" % (funcName), self.logName)

    ########################################
    def deviceStopComm(self, dev):
        funcName = inspect.stack()[0][3]
        dbFlg = False
        self.log.log(2, dbFlg, "%s called for devce %s" % (funcName, dev.name), self.logName)

        self.log.log(2, dbFlg, "%s: Resetting read loop to drop device %s" % (funcName, dev.name), self.logName)
        self.readLoop = False

        self.log.log(2, dbFlg, "%s: Completed" % (funcName), self.logName)

     ########################################
    def didDeviceCommPropertyChange(self, origDev, newDev):
        funcName = inspect.stack()[0][3]
        dbFlg = False
        self.log.log(2, dbFlg, "%s called for devce %s" % (funcName, origDev.name), self.logName)

        self.log.log(4, dbFlg, "%s: origDev:\n%s\n\nnewDev:\n%s\n" % (funcName, origDev, newDev), self.logName)

        if (origDev.pluginProps != newDev.pluginProps):
            self.log.log(2, dbFlg, "%s: Resetting read loop to include device %s" % (funcName, newDev.name), self.logName)
            self.readLoop = False

        self.log.log(2, dbFlg, "%s: Completed" % (funcName), self.logName)
        return False # Don't bother callng devStartComm or devStopComm, we took care of restarting the read loop already

    ########################################
    def deviceDeleted(self, dev):
        funcName = inspect.stack()[0][3]
        dbFlg = False
        self.log.log(2, dbFlg, "%s called for devce %s" % (funcName, dev.name), self.logName)
        self.log.log(2, dbFlg, "%s: Resetting read loop to drop device %s" % (funcName, dev.name), self.logName)
        self.readLoop = False

        self.log.log(2, dbFlg, "%s: Completed" % (funcName), self.logName)

    ########################################
    # Indigo Event Triggers: Start, Stop and Fre
    #

    ########################################
    def triggerStartProcessing(self, trigger):
        funcName = inspect.stack()[0][3]
        dbFlg = False
        self.log.log(2, dbFlg, "%s called for trigger %s" % (funcName, trigger.name), self.logName)

        self.log.log(4, dbFlg, "%s: Received trigger:%s" % (funcName, trigger), self.logName)

        self.triggerList.append(trigger.id)
        # indigoDev = indigo.devices[int(trigger.pluginProps["indigoDevice"])]
        self.triggerDict[trigger.id] = trigger.pluginProps["indigoDevice"]
        # self.triggerDict[indigoDev.name] = trigger.pluginProps["indigoDevice"]  ## Can't do ths. Two different keys in the same dict.
        # self.triggerDict["indigoDevice"] = indigoDev.name

        self.log.log(2, dbFlg, "%s trigger %s started" % (funcName, trigger.name), self.logName)
        self.log.log(2, dbFlg, "%s: Completed" % (funcName), self.logName)
 
    ########################################
    def triggerStopProcessing(self, trigger):
        funcName = inspect.stack()[0][3]
        dbFlg = False
        self.log.log(2, dbFlg, "%s called for trigger %s" % (funcName, trigger.name), self.logName)

        self.log.log(4, dbFlg, "%s: Received trigger:%s" % (funcName, trigger), self.logName)

        if trigger.id in self.triggerDict:
            self.log.log(2, dbFlg, "%s trigger %s found" % (funcName, trigger.name), self.logName)
            del self.triggerDict[trigger.id]
       
        self.log.log(2, dbFlg, "%s trigger %s deleted" % (funcName, trigger.name), self.logName)
        self.log.log(2, dbFlg, "%s: Completed" % (funcName), self.logName)
 
    ########################################
    #def triggerUpdated(self, origDev, newDev):
    #   self.log.log(4, u"<<-- entering triggerUpdated: %s" % origDev.name)
    #   self.triggerStopProcessing(origDev)
    #   self.triggerStartProcessing(newDev)

    ########################################
    def triggerEvent(self, eventId, devId):
        funcName = inspect.stack()[0][3]
        dbFlg = False
        self.log.log(2, dbFlg, "%s called" % (funcName), self.logName)
        self.log.log(3, dbFlg, "%s: received trigger %s for device %s" % (funcName, eventId, devId), self.logName)

        try:
            for trigId in self.triggerDict:
                self.log.log(3, dbFlg, "%s: found trigger ID %s" % (funcName, trigId), self.logName)
                trigger = indigo.triggers[trigId]
                self.log.log(3, dbFlg, "%s: found trigger %s" % (funcName, trigger), self.logName)
                device = self.triggerDict[trigId]
                if trigger.pluginTypeId == eventId and trigger.pluginProps['indigoDevice'] == device:
                    self.log.log(2, dbFlg, "%s: matched trigger ID %s" % (funcName, trigId), self.logName)
                    indigo.trigger.execute(trigger.id)
        except Exception, e:
                e1 = sys.exc_info()[0]
                self.log.logError("%s: Errors %s and %s" % (funcName, e, e1), self.logName)
                pass

        self.log.log(2, dbFlg, "%s: Completed" % (funcName), self.logName)

        return

    ########################################
    #  Action callbacks
    #
 
    ########################################
    def buildAction(self, event):
        funcName = inspect.stack()[0][3]
        dbFlg = True
        self.log.log(2, dbFlg, "%s called" % (funcName), self.logName)
 
        try:
            devid, event = event.split(':')
            self.log.log(3, dbFlg, "%s: Received event %s for device %s" % (funcName, event, devid), self.logName)
        except:
            self.log.logError("%s: Received bad event(1) %s for device %s" % (funcName, event, devid), self.logName)
            return

        eventList = ['commfailure', 'commok', 'doreboot', 'doshutdown', 'emergency', 'endselftest', 'failing', 'loadlimit', 'mainsback', 'offbattery', 'onbattery', 'powerout', 'remotedown', 'runlimit', 'startselftest', 'timeout']
        if event in eventList:
            self.log.log(3, dbFlg, "%s: Validated event %s for device %s" % (funcName, event, devid), self.logName)
        else:
            self.log.logError("%s: Received bad event(2) %s for device %s" % (funcName, event, devid), self.logName)
            return

        try:
                # and the reason we're taking only a numeric device id and not a string one is...
#*#                devid = int(devid)
                pass
        except ValueError:
                self.log.logError("%s: Received non-numeric device ID %s for event %s" % (funcName, devid, event), self.logName)
                return
        try:
                dev = indigo.devices[devid]
        except KeyError:
                self.log.logError("%s: Unrecognized device ID %s for event %s" % (funcName, devid, event), self.logName)
                return
        # check now to see if specified device is really a device created by this plugin...
        if dev.pluginId != self.pluginId:
                self.log.logError("%s: Device ID %s is not associated with this plugin for event %s" % (funcName, devid, event), self.logName)
                return

        action = Action()
        action.deviceId = dev.id
        action.props['actionType'] = event

        self.log.log(3, dbFlg, "%s: built action: \n%s and retrieved dev: \n%s" % (funcName, action, dev), self.logName)

        self.actionControlApcupsd(action, dev)

        self.log.log(2, dbFlg, "%s: Completed" % (funcName), self.logName)

    ########################################
    def actionControlApcupsd(self, action, dev):
        funcName = inspect.stack()[0][3]
        dbFlg = False
        self.log.log(2, dbFlg, "%s called" % (funcName), self.logName)

        self.log.log(2, dbFlg, "%s: Entered for dev: %s, and action: %s" % (funcName, dev.name, action.description), self.logName)
        self.log.log(4, dbFlg, "%s: Received action: \n%s\n and dev:\n%s" % (funcName, action, dev), self.logName)
        
        deviceId = int(action.deviceId) # Makes t easier to pass in our own events

        # All we have to do for these actons is read from the server... we will get updated states and  do the right thing automatically
        try:
           apcupsdAction = action.props['actionType']
        except:
            apcupsdAction = ''
        self.log.log(2, dbFlg, "%s: found deviceId=%s, actionType=%s" % (funcName, action.deviceId, apcupsdAction), self.logName)

        if action.pluginTypeId == 'readApcupsd':
            self.readApcupsd(dev)
        elif action.pluginTypeId == 'logStatusReport':
            sAddress = indigo.devices[int(action.deviceId)].pluginProps["apcupsdAddress"]
            sPort = indigo.devices[int(action.deviceId)].pluginProps["apcupsdPort"] 
            self.log.log(4, dbFlg, "%s: doing apcaccess status for address %s on port %s" % (funcName, sAddress, sPort), self.logName)
 
            report = os.popen(self.utility_binary + " status " + sAddress + " " + sPort).read()
            self.log.log(0, dbFlg, "\n\nFull APCUPSD Status report for %s:\n%s" % (indigo.devices[int(action.deviceId)].name, report), self.logName)
        elif apcupsdAction == 'commfailure':
            dev.setErrorStateOnServer(u'lost comm')
            self.triggerEvent(u'commfailure', deviceId)
            # self.apcupsdCommError = True ## we'll try letting readApcupsd manage this
            self.readApcupsd(dev)
        elif apcupsdAction == 'commok':
            dev.setErrorStateOnServer(None)
            self.triggerEvent(u'commok', dev.id)
            self.apcupsdCommError = True 
            self.readApcupsd(dev)
        elif apcupsdAction == 'annoyme':
            self.triggerEvent(u'annoyme', deviceId)
        elif apcupsdAction == 'battattach':
            self.triggerEvent(u'battattach', deviceId)
        elif apcupsdAction == 'battdetach':
            self.triggerEvent(u'battdetach', deviceId)
        elif apcupsdAction == 'changeme':
            self.triggerEvent(u'changeme', deviceId)
        elif apcupsdAction == 'doreboot':
            self.triggerEvent(u'doreboot', deviceId)
        elif apcupsdAction == 'doshutdown':
            self.triggerEvent(u'doshutdown', deviceId)
        elif apcupsdAction == 'emergency':
            self.triggerEvent(u'emergency', deviceId)
        elif apcupsdAction == 'endselftest':
            self.triggerEvent(u'endselftest', deviceId)
        elif apcupsdAction == 'failing':
            self.triggerEvent(u'failing', deviceId)
        elif apcupsdAction == 'killpower':
            self.triggerEvent(u'killpower', deviceId)
        elif apcupsdAction == 'loadlimit':
            self.triggerEvent(u'loadlimit', deviceId)
        elif apcupsdAction == 'mainsback':
            self.triggerEvent(u'mainsback', deviceId)
        elif apcupsdAction == 'offbattery':
            self.triggerEvent(u'offbattery', deviceId)
        elif apcupsdAction == 'onbattery':
            self.triggerEvent(u'onbattery', deviceId)
        elif apcupsdAction == 'powerout':
            self.triggerEvent(u'powerout', deviceId)
        elif apcupsdAction == 'remotedown':
            self.triggerEvent(u'remotedown', deviceId)
        elif apcupsdAction == 'runlimit':
            self.triggerEvent(u'runlimit', deviceId)
        elif apcupsdAction == 'startselftest':
            self.triggerEvent(u'startselftest', deviceId)
        elif apcupsdAction == 'timeout':
            self.triggerEvent(u'timeout', deviceId)
        elif apcupsdAction == 'readApcupsd':
            self.readApcupsd(dev)
        else:
            self.log.logError("%s: unknown action %s requested" % (funcName, apcupsdAction), self.logName)

        self.log.log(2, dbFlg, "%s: Completed" % (funcName), self.logName)

        return

    ########################################
    # UI Support
    ########################################

    ########################################
    # Button handlers
    def selectAllStates(self, valuesDict, typeId, devId):
        funcName = inspect.stack()[0][3]
        dbFlg = False
        self.log.log(2, dbFlg, "%s called" % (funcName), self.logName)

        self.log.log(2, dbFlg, "%s: received:\n>>valuesDict\n%s\n>>typeId\n%s\n>>devId\n%s\n" % (funcName, valuesDict, typeId, devId), self.logName)

        for key in valuesDict:
           if key.find('apcupsdState') != -1:
                valuesDict[key] = True

        self.log.log(2, dbFlg, "%s: Completed" % (funcName), self.logName)
        return(valuesDict)

    ########################################
    def deSelectAllStates(self, valuesDict, typeId, devId):
        funcName = inspect.stack()[0][3]
        dbFlg = False
        self.log.log(2, dbFlg, "%s called" % (funcName), self.logName)

        self.log.log(2, dbFlg, "%s: received:\n>>valuesDict\n%s\n>>typeId\n%s\n>>devId\n%s\n" % (funcName, valuesDict, typeId, devId), self.logName)

        for key in valuesDict:
           if key.find('apcupsdState') != -1:
                valuesDict[key] = False

        self.log.log(2, dbFlg, "%s: Completed" % (funcName), self.logName)
        return(valuesDict)

    ########################################
    def selectDefaultStates(self, valuesDict, typeId, devId):
        funcName = inspect.stack()[0][3]
        dbFlg = False
        self.log.log(2, dbFlg, "%s called" % (funcName), self.logName)

        self.log.log(2, dbFlg, "%s: received:\n>>valuesDict\n%s\n>>typeId\n%s\n>>devId\n%s\n" % (funcName, valuesDict, typeId, devId), self.logName)

        for key in valuesDict:
            if self.logLevel > 2: self.log.log(2, dbFlg, "%s: found valuesDict: %s" % (funcName, valuesDict[key]), self.logName)
            if key.find('apcupsdState') != -1:
                if self.logLevel > 2: self.log.log(2, dbFlg, "%s: found defaultDict: %s" % (funcName, self.defaultStatesDict[key]), self.logName)
                valuesDict[key] = self.defaultStatesDict[key]

        self.log.log(2, dbFlg, "%s: Completed" % (funcName), self.logName)
        return(valuesDict)

    ########################################
    def apcupsdBrowserOpen (self, valuesDict, typeId, devId ):
        funcName = inspect.stack()[0][3]
        dbFlg = False
        self.log.log(2, dbFlg, "%s called" % (funcName), self.logName)

        self.log.log(2, dbFlg, "%s: received:\n>>valuesDict\n%s\n>>typeId\n%s\n>>devId\n%s\n" % (funcName, valuesDict, typeId, devId), self.logName)

        self.log.log(2, dbFlg, "%s: Path=%s" % (funcName, indigo.server.getInstallFolderPath()), self.logName)
        # manual_locale = r"file:///Library/Application Support/Perceptive Automation/Indigo 6/Plugins/Plugins/apcupsd.indigoPlugin/Contents/Resources/reportFields.txt"
        docPath = r'file://' + urllib.quote(indigo.server.getInstallFolderPath()) + r'/Plugins/apcupsd.indigoPlugin/Contents/Resources/reportFields.html'
        self.log.log(2, dbFlg, "%s: Path=%s" %  (funcName, docPath), self.logName)
        indigo.activePlugin.browserOpen(docPath)

        self.log.log(2, dbFlg, "%s: Completed" % (funcName), self.logName)
        return

    ########################################
    # editing of props
    def getDeviceDisplayStateId(self, dev):
        funcName = inspect.stack()[0][3]
        dbFlg = True
        self.log.log(2, dbFlg, "%s called" % (funcName), self.logName)

        self.log.log(2, dbFlg, "%s: received device: %s" % (funcName, dev), self.logName)

        self.log.log(2, dbFlg, "%s: Completed" % (funcName), self.logName)
        return dev.pluginProps['apcupsdDevceStateDisplay'] 

   ########################################
    def getDeviceStateList(self, dev):
        funcName = inspect.stack()[0][3]
        dbFlg = False
        self.log.log(2, dbFlg, "%s called" % (funcName), self.logName)

        self.log.log(2, dbFlg, "%s: received device:\n%s\n" % (funcName, dev), self.logName)

        statesList = [] 
        stateKey = 'status'
        stateDict = {'Disabled': False, 'Key': stateKey, 'StateLabel': stateKey, 'TriggerLabel': stateKey, 'Type': 100}
        statesList.append(stateDict)

        for key in dev.pluginProps:
            if key.find('apcupsdState') != -1:
                if dev.pluginProps[key]:
                    stateKey = key[12:].lower()
                    stateDict = {'Disabled': False, 'Key': stateKey, 'StateLabel': stateKey, 'TriggerLabel': stateKey, 'Type': 100}
                    statesList.append(stateDict)

                    self.log.log(4, dbFlg, "%s: key:%s, value:%s added as state" % (funcName, key[12:], dev.pluginProps[key]), self.logName)
            else:
                self.log.log(4, dbFlg, "%s: state NOT FOUND", self.logName)

        self.log.log(3, dbFlg, "%s: returning statesList:%s" % (funcName, statesList), self.logName)

        self.log.log(2, dbFlg, "%s: Completed" % (funcName), self.logName)
        return(statesList)

    ########################################
    # UI validation
    def validateDeviceConfigUi(self, valuesDict, typeId, devId):
        funcName = inspect.stack()[0][3]
        dbFlg = False
        self.log.log(2, dbFlg, "%s called" % (funcName), self.logName)
        self.log.log(3, dbFlg, "%s: received:\n>>valuesDict\n%s\n>>typeId\n%s\n>>devId\n%s\n" % (funcName, valuesDict, typeId, devId), self.logName)

        if valuesDict[u'apcupsdAddressType'] == 'localhost':
            valuesDict[u'apcupsdAddress'] = '127.0.0.1'

        self.log.log(3, dbFlg, "%s:  returned:%s" % (funcName, valuesDict), self.logName)

        self.log.log(3, dbFlg, "%s: Completed" % (funcName), self.logName)
        return (True, valuesDict)
