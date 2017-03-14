#! /usr/bin/env python
# -*- coding: utf-8 -*-
####################
# Copyright (c) 2013, Richard Perlman All rights reserved.
# with much credit to Rob Smith (kormoc) -- https://github.com/BrightcoveOS/Diamond/blob/master/src/collectors/apcupsd/apcupsd.py
#
# Starting with 0.5.0, revised by Marty Skinner (https://github.com/MartySkinner/Indigo-apcupsd)
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
import time
import subprocess

################################################################################
# Globals
################################################################################

k_utilityBinaryName = "apcaccess"
k_utilityBinaryPath = "/usr/local/sbin:/sbin"
k_utilityCommand = "{binary} status {address} {port}".format
k_utilityOutputSeparator = ": "
k_utilityOutputSpaceReplacement = "_"
k_utilityOutputUnitWords = ['Seconds', 'Minutes', 'Hours', 'Watts', 'Volts', 'Percent']

k_eventServerBindHost = "0.0.0.0"
k_eventServerListenBacklog = 5
k_eventServerMsgMaxLength = 128 + 16 + 1 # device name + event name + separator
k_eventServerSeparator = ":"
k_eventServerEvents = ['annoyme', 'battattach', 'battdetach', 'changeme', 'commfailure', 'commok', 'doreboot', 'doshutdown', 'emergency', 'endselftest', 'failing', 'killpower', 'loadlimit', 'mainsback', 'offbattery', 'onbattery', 'powerout', 'readApcupsd', 'remotedown', 'runlimit', 'startselftest', 'timeout']

k_localhostName = u"localhost"
k_localhostAddress = "127.0.0.1"

# Increment this each time Device.xml changes / adds / deletes ANY device properties / state NAMES
k_deviceUpdateVersion = 1

def startEventServer(self, port):
    funcName = inspect.stack()[0][3]
    dbFlg = False
    self.log.log(2, dbFlg, "%s called" % (funcName), self.logName)
    self.serverRun = True
    socket.setdefaulttimeout(self.apcupsdTimeout)
    self.s = threading.Thread(target=eventServer, args=[self, k_eventServerBindHost, port])
    self.s.daemon = True
    self.s.start()
    self.sleep(5)
    if self.s.isAlive():
        self.log.log(2, dbFlg, "Event notification server started", self.logName)
        self.log.log(2, dbFlg, "%s: completed" % (funcName), self.logName)
        return True
    else:
        self.log.logError("Event notification server failed to start", self.logName)
        self.log.log(2, dbFlg, "%s: completed" % (funcName), self.logName)
        return False

def stopEventServer(self):
    funcName = inspect.stack()[0][3]
    dbFlg = False
    self.log.log(2, dbFlg, "%s called" % (funcName), self.logName)
    self.log.log(2, dbFlg, "Event notifications server asked to stop", self.logName)
    self.serverRun = False
    self.s.join(10)
    cnt = 0
    while cnt < (self.apcupsdTimeout + 10) and self.s.isAlive():
            self.sleep(1)
            cnt = cnt + 1
    self.log.log(3, dbFlg, "%s: Event notifications server needed %s delays to stop" % (funcName, cnt), self.logName)

    self.log.log(2, dbFlg, "%s: completed" % (funcName), self.logName)
    return

def eventServer(self, host, port):
    funcName = inspect.stack()[0][3]
    dbFlg = False
    self.log.log(2, dbFlg, "%s called" % (funcName), self.logName)
    self.log.log(3, dbFlg, "%s: received address: %s and port: %s" % (funcName, host, port), self.logName)

    try:
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind((host, port))
            server.listen(k_eventServerListenBacklog)
    except Exception as e:
            e1 = sys.exc_info()[0]
            self.log.logError("%s: problem with socket: %s & %s" % (funcName, e, e1), self.logName)
            return

    self.log.log(2, dbFlg, "%s: started listening on %s" % (funcName, server.getsockname()), self.logName)

    while self.serverRun:
        try:
            self.log.log(4, dbFlg, "%s: waiting for a connection" % (funcName), self.logName)
            client, client_address = server.accept()

            self.log.log(3, dbFlg, "%s: client connected from address: %s port: %s" % (funcName, client_address[0], client_address[1]), self.logName)

            if client_address[0] in self.useIpConnAccess:
                data = client.recv(k_eventServerMsgMaxLength)
                if  data:
                    self.log.log(3, dbFlg, "%s: received %s" % (funcName, data), self.logName)
                    self.buildAction(data)
            else:
                self.log.logError("%s: unauthorized client attempted access from: address: %s port: %s" % (funcName, client_address[0], client_address[1]), self.logName)

        except socket.timeout:
                pass

        except Exception as e:
                e1 = sys.exc_info()[0]
                self.log.logError("%s: read loop: Errors %s & %s" % (funcName, e, e1), self.logName)
                pass

        client.close()

    self.log.log(2, dbFlg, "%s: Event notification server closed" % (funcName), self.logName)

########################################
def findInPath(self, file_name, def_path=os.defpath):
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

########################################
def doShell(self, cmd):
        funcName = inspect.stack()[0][3]
        dbFlg = False
        self.log.log(2, dbFlg, "%s: Called" % (funcName), self.logName)
        self.log.log(3, dbFlg, "%s: command: %s" % (funcName, cmd), self.logName)

        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        out, err = p.communicate()

        self.log.log(3, dbFlg, "%s: returned output\n%s" % (funcName, out), self.logName)
        self.log.log(2, dbFlg, "%s: Completed" % (funcName), self.logName)
        return (p.returncode, out)

################################################################################
         # delayAmount : 900
            # description : plugin action
            # * deviceId : 145579207
            # pluginId : <ourPluginId>
            # * pluginTypeId : apcupsdServerEvent
            # * props : <ourPluginId> : (dict)
            #      actionType : commok (string)
            # replaceExisting : True
            # textToSpeak : 

class Action(object):
    def __init__(self):
        self.description = 'plugin generated action'
        self.deviceId = 0
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
        except KeyError:
            self.apcupsdTimeout = 8
            self.log.logError("The apcupsd plugin appears to have not been configured. Default values will be used until the configuration is changed.", self.logName)

        self.apcupsdFrequency = string.atof(self.pluginPrefs.get("apcupsdFrequency", 5))
        self.useIpConn = self.pluginPrefs.get("useIpConn", False)
        if self.useIpConn:
            self.useIpConnAccess = self.pluginPrefs.get("useIpConnAccess", k_localhostAddress).split(', ')
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
        self.nextUpdateCheck = 0  # this will force an update check as soon as the plugin is running

        self.utilityBinaryName = k_utilityBinaryName
        utilityBinaryPath = k_utilityBinaryPath
        if self.pluginPrefs.get("overridePath", False) and self.pluginPrefs.get("utilityPath", "") != "":
                utilityBinaryPath = self.pluginPrefs["utilityPath"]
        self.utilityBinary = findInPath(self, self.utilityBinaryName, utilityBinaryPath)
        if self.utilityBinaryName != self.utilityBinary:
                self.utilityBinaryFound = True
        else:
                self.utilityBinaryFound = False
                self.log.logError("Could not find the '%s' binary. Is the APCUPSD package installed?" % (self.utilityBinaryName), self.logName)

        self.removeUnits = self.pluginPrefs.get("removeUnits", True)
        self.logLevel = self.pluginPrefs.get("showDebugInfo1", 1)

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
        self.log.log(4, dbFlg, "%s:\nvaluesDict:\n%s\nUserCancelled: %s" % (funcName, valuesDict, UserCancelled), self.logName)

        if UserCancelled is False:
            self.log = logger(self)
            self.apcupsdFrequency = string.atof(valuesDict["apcupsdFrequency"])
            lastUseIpConn = self.useIpConn
            self.useIpConn = valuesDict["useIpConn"]
            if self.useIpConn:
                self.apcupsdTimeout = string.atof(valuesDict["apcupsdTimeout"])
                self.useIpConnAccess = valuesDict["useIpConnAccess"].split(', ')
                self.log.log(2, dbFlg, "%s: read access list: %s" % (funcName, self.useIpConnAccess), self.logName)
                if lastUseIpConn:
                        self.log.log(2, dbFlg, "Event notifications server asked to stop", self.logName)
                        # because we may have new preferences to put into play, ask any currently running server to stop what its doing
                        stopEventServer(self)
                port = int(valuesDict["useIpConnPort"])
                startEventServer(self, port)
            else:
                # since we don't need a server now, ask any currently running server to stop what its doing
                stopEventServer(self)

            daysBetweenUpdateChecks = string.atoi(valuesDict["daysBetweenUpdateChecks"])
            self.secondsBetweenUpdateChecks = daysBetweenUpdateChecks * 86400
            self.nextUpdateCheck = 0        # this will force an update check starting now
            self.logLevel = string.atoi(valuesDict["showDebugInfo1"])

            if valuesDict["overridePath"] and valuesDict["utilityPath"] != "":
                utilityBinaryPath = valuesDict["utilityPath"]
                utilityBinary = findInPath(self, self.utilityBinaryName, utilityBinaryPath)
                if self.utilityBinaryName != utilityBinary:
                        self.utilityBinaryPath = utilityBinary

            self.log.log(1, dbFlg, "Plugin options reset. Polling apcupsd servers every %s minutes and a debug level of %i" % (self.apcupsdFrequency, int(valuesDict["showDebugInfo1"])), self.logName)
        self.log.log(2, dbFlg, "%s: Completed" % (funcName), self.logName)

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
        if self.utilityBinaryFound is False:
                self.log.log(2, dbFlg, "%s: A missing '%s' binary will NOT clear itself without changing the plugin preferences and/or installing the APCUPSD package, then reloading the plugin." % (funcName, self.utilityBinaryName), self.logName)
                self.sleep(60*10)
                self.log.log(2, dbFlg, "%s: Completed" % (funcName), self.logName)
                return

        if self.useIpConn:
            port = int(self.pluginPrefs["useIpConnPort"])
            startEventServer(self, port)

        try:
            self.log.log(1, dbFlg, "Plugin started. Polling apcupsd server(s) every %s minutes" %  (self.apcupsdFrequency), self.logName)
        except:
            self.log.logError("Plugin start delayed pending completion of initial plugin configuration", self.logName)
            return

        try:
            while True:
                self.readLoop = True
                if self.secondsBetweenUpdateChecks > 0:
                        # obtain the current date/time and determine if it is after the previously-calculated
                        # next check run
                        timeNow = time.time()
                        if timeNow > self.nextUpdateCheck:
                                self.pluginPrefs['updaterLastCheck'] = timeNow
                                self.log.log(3, dbFlg, "# of seconds between update checks: %s" % (int(self.secondsBetweenUpdateChecks)), self.logName)
                                self.nextUpdateCheck = timeNow + self.secondsBetweenUpdateChecks
                                # use the updater to check for an update now
                                self.checkForUpdates()

                devCount = 0
                for dev in indigo.devices.iter(self.pluginId):
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

                # we sleep (apcupsdFrequency minutes) between reads - in 1 sec increments so we can be interupted by self.readLoop changing
                count = 0
                while count < self.apcupsdFrequency * 60 and self.readLoop:
                    self.sleep(1)
                    count +=1

        except self.StopThread:
            self.log.log(2, dbFlg, "%s: StopThread is now True" % (funcName), self.logName)
            stopEventServer(self)

        self.log.log(2, dbFlg, "%s: Completed" % (funcName), self.logName)

    ########################################
    def readApcupsd(self, dev, parseOnly=False, tmpProps=False):
        funcName = inspect.stack()[0][3]
        dbFlg = False
        self.log.log(2, dbFlg, "%s called" % (funcName), self.logName)
        self.log.log(4, dbFlg, "%s: Received device:\n%s\n" % (funcName, dev), self.logName)

        if tmpProps is False:
                try:
                        sAddress = dev.pluginProps["apcupsdAddress"]
                except KeyError:
                        self.log.logError("%s: Trying to get status for a device that is not configured" % (funcName), self.logName)
                        self.log.log(2, dbFlg, "%s: Completed" % (funcName), self.logName)
                        return False
                sPort = dev.pluginProps["apcupsdPort"]
        else:
                sAddress = tmpProps["apcupsdAddress"]
                sPort = tmpProps["apcupsdPort"]
        self.log.log(4, dbFlg, "%s: doing '%s status' for address %s on port %s" % (funcName, self.utilityBinary, sAddress, sPort), self.logName)

        apcupsdSuccess = False
        apcupsdRetries = 0

        while not apcupsdSuccess and apcupsdRetries < 5:
            if apcupsdRetries == 0:
                self.log.log(3, dbFlg, "%s: starting read. Retries=%s" % (funcName, apcupsdRetries), self.logName)
            else:
                self.log.log(2, dbFlg, "%s: starting read. Retries=%s" % (funcName, apcupsdRetries), self.logName)

            apcupsdRetries = apcupsdRetries + 1

            result, report = doShell(self, k_utilityCommand(binary=self.utilityBinary, address=sAddress, port=sPort))
            if result:
                self.log.logError("%s: Connection to %s failed with error code %s. Attempt %s of 5" % (funcName, self.utilityBinary, result, apcupsdRetries), self.logName)
                self.log.logError("%s: Returned output: %s" % (funcName, report), self.logName)
                apcupsdSuccess = False
                self.sleep(1)
            else:
                self.log.log(4, dbFlg, "%s: report\n%s" % (funcName, report), self.logName)

                metrics = {}

                for line in report.split('\n'):
                    (key,spl,val) = line.partition(k_utilityOutputSeparator)
                    # if the key contains any spaces, they would be unable to be specified in Devices.XML as field Ids so replace now
                    key = key.rstrip().lower().replace(' ', k_utilityOutputSpaceReplacement)
                    val = val.strip()
                    if self.removeUnits is True:
                        test = val.split()
                        if len(test) >= 2:
                            unit = test[1] # is there a "units" keyword here?
                            if unit in k_utilityOutputUnitWords:
                                val = test[0]  # ignore anything after 1st space
                    if key != '':
                        metrics[key] = val
                        self.log.log(4, dbFlg, "%s: parsed key=%s and val=%s" % (funcName, key, val), self.logName)

                if 'status' in metrics:
                    apcupsdSuccess = True
                    if parseOnly:
                            self.log.log(2, dbFlg, "%s: Completed" % (funcName), self.logName)
                            return (True, metrics)

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
                else:
                        self.log.log(2, dbFlg, "%s: Completed" % (funcName), self.logName)
                        return (False, metrics)

        if apcupsdSuccess:
            for metric in metrics:
                value = metrics[metric]
                try:
                    if metric in dev.states:
                        self.log.log(4, dbFlg, "%s: found metric: %s " % (funcName, metric), self.logName)

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

                        self.log.log(4, dbFlg, "%s: metric:%s, val:%s, is Error:%s" % (funcName, metric, value, self.apcupsdCommError), self.logName)
                except:
                    self.log.logError("%s: error writing device state" % (funcName), self.logName)

            self.log.log(2, dbFlg, "%s: Completed readings update from device: %s" % (funcName, dev.name), self.logName)
        else:
            self.log.logError("%s: Failed to get status for UPS %s after %s tries. Will retry in %s minutes" % (funcName, dev.name, apcupsdRetries, self.apcupsdFrequency), self.logName)
        self.log.log(2, dbFlg, "%s: Completed" % (funcName), self.logName)

    ########################################
    # Device start, stop, modify and delete
    ########################################
    def deviceStartComm(self, dev):
        funcName = inspect.stack()[0][3]
        dbFlg = False
        self.log.log(2, dbFlg, "%s called for device %s" % (funcName, dev.name), self.logName)

        madeChanges = False
        tmpProps = dev.pluginProps
        deviceVersion = int(tmpProps.get('version', 0))
        if deviceVersion < 1:
                madeChanges = True
                # check to see if we have any of the older, misspelled property names and change to the correct ones if we do
                try:
                    tmp = tmpProps['apcupsdDevceStateDisplay']
                    tmpProps['apcupsdDeviceStateDisplay'] = tmp
                    del tmpProps['apcupsdDevceStateDisplay']
                except KeyError:
                    pass
                try:
                    tmp = tmpProps['apcupsdstatealarmdel']
                    tmpProps['apcupsdStateALARMDEL'] = tmp
                    del tmpProps['apcupsdstatealarmdel']
                except KeyError:
                    pass

        # continue with testing deviceVersion < 2, etc. as needed

        # and if we have any "forced" updates to made regardless of versions (usually only seen in development)...
#        try:
#                del tmpProps['apcupsdstatealarmdel']
#                madeChanges = True
#        except:
#                pass

        if madeChanges is True:
            self.log.log(1, dbFlg, "%s: Device %s updated to version %s" % (funcName, dev.name, k_deviceUpdateVersion), self.logName)
            tmpProps['version'] = k_deviceUpdateVersion
            dev.replacePluginPropsOnServer(tmpProps)

        if dev.enabled and not self.startingUp:
            self.log.log(2, dbFlg, "%s: Resetting read loop to include device %s" % (funcName, dev.name), self.logName)
            self.readLoop = False

        self.log.log(2, dbFlg, "%s: Completed" % (funcName), self.logName)

    ########################################
    def deviceStopComm(self, dev):
        funcName = inspect.stack()[0][3]
        dbFlg = False
        self.log.log(2, dbFlg, "%s called for device %s" % (funcName, dev.name), self.logName)

        self.log.log(2, dbFlg, "%s: Resetting read loop to drop device %s" % (funcName, dev.name), self.logName)
        self.readLoop = False

        self.log.log(2, dbFlg, "%s: Completed" % (funcName), self.logName)

     ########################################
    def didDeviceCommPropertyChange(self, origDev, newDev):
        funcName = inspect.stack()[0][3]
        dbFlg = False
        self.log.log(2, dbFlg, "%s called for device %s" % (funcName, origDev.name), self.logName)

        self.log.log(4, dbFlg, "%s: origDev:\n%s\n\nnewDev:\n%s\n" % (funcName, origDev, newDev), self.logName)

        if (origDev.pluginProps != newDev.pluginProps):
            self.log.log(2, dbFlg, "%s: Resetting read loop to include device %s" % (funcName, newDev.name), self.logName)
            self.readLoop = False

        self.log.log(2, dbFlg, "%s: Completed" % (funcName), self.logName)
        return False  # Don't bother callng devStartComm or devStopComm, we took care of restarting the read loop already

    ########################################
    def deviceDeleted(self, dev):
        funcName = inspect.stack()[0][3]
        dbFlg = False
        self.log.log(2, dbFlg, "%s called for device %s" % (funcName, dev.name), self.logName)
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
        except Exception as e:
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
        dbFlg = False
        self.log.log(2, dbFlg, "%s called" % (funcName), self.logName)

        try:
            devid, event = event.split(k_eventServerSeparator)
            self.log.log(3, dbFlg, "%s: Received event %s for device %s" % (funcName, event, devid), self.logName)
        except:
            self.log.logError("%s: Received bad event(1) %s for device %s" % (funcName, event, devid), self.logName)
            return

        if event in k_eventServerEvents:
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
        action.pluginId = self.pluginId
        action.deviceId = dev.id
        action.props['actionType'] = event

        self.log.log(4, dbFlg, "%s: built action: \n%s and retrieved dev: \n%s" % (funcName, action, dev), self.logName)

        self.actionControlApcupsd(action, dev)

        self.log.log(2, dbFlg, "%s: Completed" % (funcName), self.logName)

    ########################################
    def actionControlApcupsd(self, action, dev):
        funcName = inspect.stack()[0][3]
        dbFlg = False
        self.log.log(2, dbFlg, "%s called" % (funcName), self.logName)

        self.log.log(2, dbFlg, "%s: Entered for dev: %s, and action: %s" % (funcName, dev.name, action.description), self.logName)
        self.log.log(4, dbFlg, "%s: Received action: \n%s\n and dev:\n%s" % (funcName, action, dev), self.logName)

        deviceId = int(action.deviceId) # Makes it easier to pass in our own events

        # All we have to do for these actons is read from the server... we will get updated states and do the right thing automatically
        try:
           apcupsdAction = action.props['actionType']
        except KeyError:
            apcupsdAction = ''
        self.log.log(2, dbFlg, "%s: found deviceId=%s, actionType=%s" % (funcName, action.deviceId, apcupsdAction), self.logName)

        if action.pluginTypeId == 'readApcupsd':
            self.readApcupsd(dev)
        elif action.pluginTypeId == 'logStatusReport':
            sAddress = indigo.devices[int(action.deviceId)].pluginProps["apcupsdAddress"]
            sPort = indigo.devices[int(action.deviceId)].pluginProps["apcupsdPort"]
            self.log.log(4, dbFlg, "%s: doing '%s status' for address %s on port %s" % (funcName, self.utilityBinary, sAddress, sPort), self.logName)

            result, report = doShell(self, k_utilityCommand(binary=self.utilityBinary, address=sAddress, port=sPort))
            self.log.log(0, dbFlg, "\n\nFull APCUPSD Status report for %s:\n%s" % (indigo.devices[int(action.deviceId)].name, report), self.logName)
        elif apcupsdAction == 'commfailure':
            dev.setErrorStateOnServer(u'lost comm')
            self.triggerEvent(u'commfailure', deviceId)
            # self.apcupsdCommError = True  ## we'll try letting readApcupsd manage this
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

        self.log.log(4, dbFlg, "%s: received:\n>>valuesDict\n%s\n>>typeId\n%s\n>>devId\n%s\n" % (funcName, valuesDict, typeId, devId), self.logName)

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

        self.log.log(4, dbFlg, "%s: received:\n>>valuesDict\n%s\n>>typeId\n%s\n>>devId\n%s\n" % (funcName, valuesDict, typeId, devId), self.logName)

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

        self.log.log(4, dbFlg, "%s: received:\n>>valuesDict\n%s\n>>typeId\n%s\n>>devId\n%s\n" % (funcName, valuesDict, typeId, devId), self.logName)

        for key in valuesDict:
            if key.find('apcupsdState') != -1:
                try:
                        defaultState = self.defaultStatesDict[key]
                        self.log.log(3, dbFlg, "%s: using '%s' default of %s" % (funcName, key, self.defaultStatesDict[key]), self.logName)
                except KeyError:
                        self.log.log(3, dbFlg, "%s: missing entry '%s' in defaultStates.dict, defaulting to False" % (funcName, key), self.logName)
                        defaultsState = False
                valuesDict[key] = defaultState

        self.log.log(2, dbFlg, "%s: Completed" % (funcName), self.logName)
        return(valuesDict)

    ########################################
    def selectQueryDevice(self, valuesDict, typeId, devId):
        funcName = inspect.stack()[0][3]
        dbFlg = False
        self.log.log(2, dbFlg, "%s called" % (funcName), self.logName)

        self.log.log(4, dbFlg, "%s: received:\n>>valuesDict\n%s\n>>typeId\n%s\n>>devId\n%s\n" % (funcName, valuesDict, typeId, devId), self.logName)

        for key in valuesDict:
           if key.find('apcupsdState') != -1:
                valuesDict[key] = False

        tmpProps = indigo.Dict()
        tmpProps['apcupsdAddress'] = valuesDict['apcupsdAddress']
        if valuesDict['apcupsdAddressType'] == k_localhostName or tmpProps['apcupsdAddress'] == "":
                tmpProps['apcupsdAddress'] = k_localhostAddress
        tmpProps['apcupsdPort'] = valuesDict['apcupsdPort']
        self.log.log(4, dbFlg, "%s: temporary properties for new device\n%s\n" % (funcName, tmpProps), self.logName)

        (returnStatus, metrics) = self.readApcupsd(0, True, tmpProps)
        if returnStatus == True:
                self.log.log(4, dbFlg, "%s: returned\n>>device values\n%s\n" % (funcName, metrics), self.logName)
                for metric in metrics:
                        key = "apcupsdState" + metric.upper()
                        try:
                                if key in valuesDict:
                                        self.log.log(3, dbFlg, "%s: found matching state: %s" % (funcName, metric), self.logName)
                                        valuesDict[key] = True
                        except:
                                pass
        else:
                self.log.log(1, dbFlg, "%s: Cannot determine which states the device might provide" % (funcName), self.logName)

        self.log.log(2, dbFlg, "%s: Completed" % (funcName), self.logName)
        return(valuesDict)

    ########################################
    # editing of props
    def getDeviceDisplayStateId(self, dev):
        funcName = inspect.stack()[0][3]
        dbFlg = False
        self.log.log(2, dbFlg, "%s called" % (funcName), self.logName)

        self.log.log(4, dbFlg, "%s: received device:\n%s\n" % (funcName, dev), self.logName)

        self.log.log(2, dbFlg, "%s: Completed" % (funcName), self.logName)
        try:
            return dev.pluginProps['apcupsdDeviceStateDisplay']
        except KeyError:
            return None

   ########################################
    def getDeviceStateList(self, dev):
        funcName = inspect.stack()[0][3]
        dbFlg = False
        self.log.log(2, dbFlg, "%s called" % (funcName), self.logName)

        self.log.log(4, dbFlg, "%s: received device:\n%s\n" % (funcName, dev), self.logName)

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

                    self.log.log(4, dbFlg, "%s: %s added as state" % (funcName, key[12:]), self.logName)
            else:
                self.log.log(4, dbFlg, "%s: %s property is not a state" % (funcName, key[12:]), self.logName)

        self.log.log(3, dbFlg, "%s: returning statesList: %s" % (funcName, statesList), self.logName)

        self.log.log(2, dbFlg, "%s: Completed" % (funcName), self.logName)
        return(statesList)

    ########################################
    # UI validation for devices
    def validateDeviceConfigUi(self, valuesDict, typeId, devId):
        funcName = inspect.stack()[0][3]
        dbFlg = False
        self.log.log(2, dbFlg, "%s called" % (funcName), self.logName)
        self.log.log(4, dbFlg, "%s: received:\n>>valuesDict\n%s\n>>typeId\n%s\n>>devId\n%s\n" % (funcName, valuesDict, typeId, devId), self.logName)

        if valuesDict['apcupsdAddressType'] == k_localhostName or valuesDict['apcupsdAddress'] == '':
            valuesDict['apcupsdAddress'] = k_localhostAddress
        self.log.log(4, dbFlg, "%s: returned:\n>>valuesDict\n%s\n" % (funcName, valuesDict), self.logName)

        self.log.log(2, dbFlg, "%s: Completed" % (funcName), self.logName)
        return (True, valuesDict)

    ########################################
    # UI validation for the plugin configuration
    def validatePrefsConfigUi(self, valuesDict):
        funcName = inspect.stack()[0][3]
        dbFlg = False
        validationErr = False
        errorDict = indigo.Dict()
        self.log.log(2, dbFlg, "%s called" % (funcName), self.logName)
        self.log.log(4, dbFlg, "%s: received:\n>>valuesDict\n%s\n" % (funcName, valuesDict), self.logName)

        if valuesDict["overridePath"] and valuesDict["utilityPath"] != "":
                utilityBinaryPath = valuesDict["utilityPath"]
                utilityBinary = findInPath(self, self.utilityBinaryName, utilityBinaryPath)
                if self.utilityBinaryName == utilityBinary:
                        validationErr = True
                        errorDict["utilityPath"] = "'%s' utility not found in this path" % (self.utilityBinaryName)
                        errorDict["showAlertText"] = "You must specify the UNIX-style path to the '%s' binary." % (self.utilityBinaryName)

        self.log.log(4, dbFlg, "%s: returned:\n>>valuesDict\n%s\n" % (funcName, valuesDict), self.logName)

        self.log.log(2, dbFlg, "%s: Completed" % (funcName), self.logName)
        if validationErr is False:
                return (True, valuesDict)
        else:
                return (False, valuesDict, errorDict)
