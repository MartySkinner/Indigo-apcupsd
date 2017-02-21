# acpupsd Plugin

> Because of the volatile nature of individual components within GitHub repositories such as this one, [__please only download actual releases__](../../releases). Any other downloads may result in an incomplete plugin, repeated errors in the Indigo log and/or incorrect behavior of the plugin.

> Note: This plugin **requires** the separate apcupsd software package (<http://www.apcupsd.org>) to be installed and running on whatever machine your APC UPS is connected to.

This is a software plugin for the [Indigo home automation software](http://www.indigodomo.com). The plugin allows access to the current state information for many models of [APC](http://www.apc.com) UPSes.

Unless otherwise noted, this plugin's releases should work without modifications with Indigo 6 and Indigo 7. With Indigo 5, minor steps after the plugin has been installed must be performed—[see below](#installing-and-using-the-plugin-on-indigo-5). It is possible the plugin might work in earlier versions of Indigo but no testing has been done on them.

## Upgrading from Versions Below 0.5.0

If you are running a previous version lower than 0.5.0 you will need to take a few extra steps to migrate to the newer version. This should be a one-time activity, although future versions may have their own set of migration steps.

1. Run the Indigo client on the Indigo server system.
1. Select the __Plugins &mdash;> apcupsd &mdash;> Disable__ menu option to disable the older plugin.
1. [Download the updated plugin](../../releases).
1. In the __Finder__:
  * If the download doesn't automatically expand, double-click on the newly downloaded __.zip__ file (__apcupsd.indigoPlugin.zip__).
  * Double-click on __apcupsd.indigoPlugin__.
1. Follow the Indigo prompts for upgrading and enabling the plugin.
1. That should re-enable the plugin but if not, select the __Plugins &mdash;> apcupsd &mdash;> Enable__ menu option.
1. Setup the overall plugin settings (see [Plugin Configuration](#plugin-configuration) below).
1. Reconnect Indigo UPS devices to the new plugin. For each such device in the Indigo client DEVICES listing:
  * Double-click the device name.
  * The __Plugin:__ selector should be empty. Choose __apcupsd__ from the popup list.
  * Set the __Model:__ as __apcupsd UPS__.
  * Click the __Edit Device Settings...__ button.
  * Optional: click the __Query UPS for states__ button to match up the monitored states to the UPS.
  * Review the enabled state names.
  * Even if you didn't change anything, click Save on the __Configure apcupsd UPS__ dialog.
  * Click OK on the __Edit Device__ dialog.

This should refresh your Indigo UPS device states, while retaining associated triggers, state condition tests, etc. Should these steps not work you will need to delete the UPS device(s) and recreate them.

## Plugin Configuration

After you install the plugin you will need to configure it. These settings apply to all UPS devices monitored by this plugin. You may need to scroll the dialog's contents to see all the settings. In the __Configure apcupsd__ dialog (__Plugins &mdash;> apcupsd &mdash;> Configure...__ menu option) you:

* Set the frequency at which the Indigo devices should be queried and their state values updated. The default is every 5 minutes.
* Decide if you want reported "units" (Minutes, Hours, Percent, etc.) to be removed from the device's state values. The default is "checked" (this makes it easier for device state comparisons).
* Set the frequency for plugin software update checking. The default is every day.
* See the [Event Notifications](#event-notifications) section below for setting the __Use event server for external event notifications__ checkbox. The default is "unchecked."
* Decide if you need to override the location of the __apcaccess__ utility in the separate apcupsd package. The default is "unchecked". This is an advanced feature and should remain "unchecked" unless the plugin cannot locate this utility.
* Set a logging level. The default is level 1.
* Click Save.
![Plugin Configuration](doc-images/plugin_config.png)

All items on the __Configure apcupsd__ dialog include tooltips—just hover over an item of interest for a quick reminder of its purpose.


Once configured, the plugin will allow you to create an Indigo device for each apcupsd instance (IP address and port) you have for your attached UPSes.

## Device Configuration

When creating an apcupsd plugin device, you:

* Provide an IP address. If you have the apcupsd software package running on the same machine as your Indigo server, select the default **local host**. Otherwise select **Will Specify** and enter the remote IP address in the textfield that appears.
* Enter the port number. The default of 3551 should be correct for most installations.
* Select the UPS report fields you wish to use for states in this device. The default set contains the fields that are likely to be of interest. Buttons are available to:
  - __Query UPS for states__ (clears state checkboxes this UPS does not support, and sets those that it does)
  - __Select all states__ (fields)
  - __Deselect all states__ (fields)
  - __Reset default states__ from a built-in list in the plugin
* Specify the state (field) to be displayed for this device in the Indigo client's DEVICES listing State column. The default is __status__.
* Click Save.
![Device Configuration](doc-images/device_config.png)

All items on the __Configure apcupsd UPS__ dialog include tooltips—just hover over an item of interest for a quick reminder of its purpose.

## Event Notifications

The separate apcupsd package provides a mechanism to perform site-specific steps when certain events are detected on a monitored UPS. One such step can be to send a notification to the Indigo server. This plugin contains an event notification server to receive those event notifications from the local apcupsd process, via its __/etc/apcupsd/apccontrol__ shell script, and from instances of apcupsd running on remote systems via the same mechanism. This event server is __not__ required to be used *unless* you plan to have the Indigo server react to UPS changes via triggers.

To enable the event server in the __Plugins &mdash;> apcupsd &mdash;> Configure...__ dialog:

* Click the __Use event server for external event notifications__ checkbox.
* Enter the local TCP port to listen on. This must be an unused port on the Indigo Server—15006 is used as an example.
* Enter a comma separated list of IP addresses from which incoming event connections can be accepted. If you are running apcupsd on the local host, be sure to include 127.0.0.1.

The screenshot in the [Plugin Configuration](#plugin-configuration) section shows this feature enabled.

To send these external events to the plugin's event server, you need to edit the desired event handler files in __/etc/apcupsd/__*filename*. The following handlers (*filename* __must__ match these names) are supported (create them if they do not exist and you want to receive that event in Indigo):

* annoyme
* battattach
* battdetach
* changeme
* commfailure
* commok
* doreboot
* doshutdown
* emergency
* endselftest
* failing
* killpower
* loadlimit
* mainsback
* offbattery
* onbattery
* powerout
* readApcupsd (not used by apcupsd/apccontrol, but can be used as a test event script)
* remotedown
* runlimit
* startselftest
* timeout

Add the following text to each handler file you wish to have send events to the Indigo apcupsd plugin:

    #!/bin/sh
    
    EVENT=`basename $0`
    UPS=12345678
    
    /bin/echo -n "${UPS}:${EVENT}" |/usr/bin/nc -w1 127.0.0.1 15006 &

Make sure you enter the Indigo device ID for your UPS device as the value of the UPS variable in the script.

If you are comfortable with the command line interface of your Mac, you may wish to delete all but one of the handler files and then create them all again but as symlinks (not Finder aliases) to the one file you saved. In that way, you only need to edit one file to change all of the handlers.

## Installing and Using the Plugin on Indigo 5

Because Indigo 5 uses an older of Python for its plugin execution, some minor code changes must be made to the plugin distribution to work with that older version of Python. __These changes must be made any time the plugin is updated on your Indigo 5 system.__ Without making these code changes the plugin __will not__ function properly and will log errors to the Indigo log on an on-going basis.

1. Select the __Plugins &mdash;> apcupsd &mdash;> Disable__ menu option.
1. On the Indigo server system, open a Terminal (__/Applications/Utilities/Terminal__) window and issue these commands one at a time (please use Cut from this document and Paste each line into the Terminal window):

    `cd /Library/Application\ Support/Perceptive\ Automation/Indigo\ 5/Plugins\ \(Disabled\)/apcupsd.indigoPlugin/Contents/Server\ Plugin/`

    `sed -e "s/\(.*except .*\)\( as \)\(.*:\)$/\1, \3/" -i .2.6 *.py`
1. Select the __Plugins &mdash;> apcupsd &mdash;> Enable__ menu option.
1. Proceed with setting up the [Plugin Configuration](#plugin-configuration) and the [Device Configuration](#device-configuration) for your UPSes.

## Troubleshooting and Discussions

Please use the [APCUPSD Plugin discussion forum thread](http://www.perceptiveautomation.com/userforum/viewtopic.php?f=22&t=10707) to post any issues, questions, ideas, etc.

## License

This project is licensed using [Unlicense](http://unlicense.org/).

## Plugin ID

Here is the plugin ID in case you need to programmatically restart the plugin:

**Plugin ID**: com.martys.apcupsd

