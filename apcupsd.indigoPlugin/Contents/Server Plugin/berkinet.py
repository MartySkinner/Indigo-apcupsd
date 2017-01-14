#!/usr/bin/env python2.5
# Filename: berkinet.py

import indigo
import re
import socket
from urllib2 import urlopen

########################################
def versionCheck(self, pluginDisplayName, logLevel, pluginId, pluginVersion):	
	if logLevel > 1: self.debugLog(u"versionCheck() called")
	sp = re.split('\.', pluginId)
	myName = sp[2]
	myVersion = str(pluginVersion)
	versionServer = 'http://yikes.com/plugins/'
	theUrl = versionServer + myName + '.html'
	if logLevel > 2: indigo.server.log('url:%s' % theUrl, type=pluginDisplayName)
	socket.setdefaulttimeout(3)
	try:
		f = urlopen(theUrl)
		latestVersion = str(f.read()).rstrip('\n')
		if myVersion < latestVersion:
			self.errorLog(u"You are running v%s. A newer version, v%s is available." \
				% (myVersion, latestVersion))
		else:
			if logLevel > 0: indigo.server.log(u'Your plugin version, v%s, is current.' % \
				myVersion, type=self.pluginDisplayName)
	except:
		self.errorLog(u"Unable to reach the version server.")
	

##########################################################################################
# logger class for Indigo Plugins.  Originally written by berkinet, modified by Travis, and modified even more by berkinet
#
# Usage:
#
#
#	1. 	Create an instance.  It will check the pluginPrefs for the showDebugInfo1
#		log level setting.
#			self.logger = indigoPluginUtils.logger(self)
#
#	2.	Log like so.  The first argument is the log level, second is the log.
#		It will only log the message if the message's log level is <= logLevel.
#		self.logger.log(1, False, "Bla bla", type)
#
#	3.  To log errors:
#		self.logger.logError("Oops, error", type)
#
#	4.  To read the loggers log level in the plugin:
#		logLevel = self.logger.logLevel
#

class logger(object):

	def __init__(self, plugin):
		self.plugin = plugin
		self.logLevel = None
		self.readConfig()


	def readConfig(self):
		kLogLevelList = ['None', 'Normal', 'Verbose', 'Debug', 'Intense Debug']

		# Save current log level
		oldLevel = self.logLevel
		# Get new log level from prefs, default to 1 if not found
		self.logLevel = int(self.plugin.pluginPrefs.get("showDebugInfo1", "1"))

		# Validate log level
		if self.logLevel > 4:
			self.logLevel = 1

		# Enable debugging?
		if self.logLevel > 2:
			self.plugin.debug = True
		else:
			self.plugin.debug = False

		# If this is the first run
		if(oldLevel is None):
			self.log(0, False, "Log level preferences are set to \"%s\"." % kLogLevelList[self.logLevel], self.plugin.pluginDisplayName)
		# or are we just checking for a change in log level
		elif oldLevel != self.logLevel:
			self.log(1, "Log level preferences changed to \"%s\"." % kLogLevelList[self.logLevel], self.plugin.pluginDisplayName)


	def log(self, level, override, logMsg, type):
		# indigo.server.log('received: %s, %s, %s, %s, %s' % ( level, self.logLevel, override, logMsg, type), type='TESTING')
		if level <= self.logLevel or override:
			# if level < 3:
			indigo.server.log(logMsg, type=type)
			# else:
			# 	type = type + " DEBUG"
			# 	indigo.server.log(logMsg, type)


	def logError(self, logMsg, type):
		indigo.server.log(logMsg, type=type, isError=True)

	
