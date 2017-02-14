#! /usr/bin/env python
# -*- coding: utf-8 -*-

prId = "com.martys.apcupsd"
apcupsdPlugin = indigo.server.getPlugin(prId)
cnt = 0
for device in indigo.devices.iter(prId):
    if device.enabled:
        apcupsdPlugin.executeAction("logStatusReport", deviceId=device.id)
        indigo.server.log("End of full status report for all enabled UPSs", type='apcupsd')
        cnt = cnt + 1
if cnt == 0:
        indigo.server.log("Did not find any matching enabled UPS devices", type='apcupsd')

