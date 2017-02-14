#! /usr/bin/env python
# -*- coding: utf-8 -*-

prId = "com.martys.apcupsd"
apcupsdPlugin = indigo.server.getPlugin(prId)
cnt = 0
for device in indigo.devices.iter(prId):
    if device.enabled:
        apcupsdPlugin.executeAction("readApcupsd", deviceId=device.id)
        indigo.server.log("Refreshed data for device name %s" % (device.name), type='apcupsd')
        cnt = cnt + 1
if cnt == 0:
        indigo.server.log("Did not find any matching enabled UPS devices", type='apcupsd')
