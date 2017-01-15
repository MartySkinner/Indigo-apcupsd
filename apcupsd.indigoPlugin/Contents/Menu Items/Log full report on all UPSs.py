#! /usr/bin/env python
# -*- coding: utf-8 -*-

prId = "com.berkinet.apcupsd"
apcupsdPlugin = indigo.server.getPlugin(prId)
for device in indigo.devices.iter(prId):
    if device.enabled:
        apcupsdPlugin.executeAction("logStatusReport", deviceId=device.id)
        indigo.server.log("Wrote full status report for all UPSs to the Indigo log", type='apcupsd')
