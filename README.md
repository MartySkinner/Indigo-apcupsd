Note: This plugin **requires** apcupsd (http://www.apcupsd.org) to be installed and running on whatever machine your UPS is connected to.

When you install the plugin you will need to configure it. In the Plugin configuration dialog set the frequency at which the Indigo devices should be updated, a connection timeout, and a debugging level.

Once configured plugin will allow you to create an Indigo device for each apcupsd instance (IP Address & Port) you have.

When creating an apcupsd plugin device, you need to:
* Provide an IP Address. If you have apcupsd running on the same machine as your Indigo server, select the default **local host**. Otherwise select **Will Specify** and enter the IP Address in textfield that appears.
* Enter the port number. The default of 3551 should be correct for most installations.
* Select the UPS Report Fields you wish to use for states in this device. The default set contains the fields that are most likely to be of interest. Buttons are available to:
  - Select all states (fields)
  - Deselect all states (fields)
  - Reset default states list (i.e. Reset)
* Specify the state (field) to be displayed for this device in Indigo's Devices window State column
* Click Save


This release contains a built-in IP server to receive event notifications from the local apcupsd, and instances of apcupsd running on remote hardware. This feature is in addition to the Event Notification feature available in release 0.3.3, but is designed to ultimately replace that implementation.

To enable the new event server click the Use IP Socket for events? checkbox in the Plugin Config Dialog. Then enter the local IP port to listen on and a comma separated list of IP addresses from which incoming connections can be accepted. If you are running apcupsd on the local host, be sure to include 127.0.0.1. Here is a screenshot showing an example of the IP server config:

<picture>

To send events to the event server, you need to edit the event handlers in /etc/apcupsd. The following handlers are supported:
commfailure, commok, doreboot, doshutdown, emergency, endselftest, failing, loadlimit, mainsback, offbattery, onbattery, powerout, remotedown, runlimit, startselftest and timeout

Add the following text to each file you wish to have send events to the Indigo apcupsd plugin:

\#!/bin/sh

EVENT=`basename $0`
UPS=12345678

/bin/echo -n "${UPS}:${EVENT}" |/usr/bin/nc -w1 127.0.0.1 15006 &

Make sure you enter the Indigo device ID for your UPS device as the value of the UPS variable in the script.

If you are comfortable with the shell, you may wish to delete all but one of the handler files and then create them all again but as hard links to the one file you saved. In that way, you only need to edit one file to change all of the handlers.

Please use the [apcupsd plugin discussion forum](http://www.perceptiveautomation.com/userforum/viewtopic.php?f=22&t=10707 to post any issues, questions, ideas, etc.
