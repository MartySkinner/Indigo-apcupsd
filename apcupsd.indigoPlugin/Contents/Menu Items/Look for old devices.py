#! /usr/bin/env python
# -*- coding: utf-8 -*-

prId = 'com.berkinet.apcupsd'
cnt = 0

indigo.server.log("Starting scan for '%s' devices" % (prId), type='apcupsd')

for device in indigo.devices.iter(prId):
        deviceId = device.id
        indigo.server.log("Found device name '%s' id %s" % (device.name, deviceId), type='apcupsd')
        cnt = cnt + 1
        for trigger in indigo.triggers.iter():
                try:
                        if trigger.deviceId == deviceId:
                                indigo.server.log("Found associated trigger '%s'" % (trigger.name), type='apcupsd')
                except:
                        pass

if cnt == 0:
        indigo.server.log("Did not find any matching devices", type='apcupsd')
