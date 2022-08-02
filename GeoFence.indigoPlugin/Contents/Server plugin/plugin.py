#! /usr/bin/env python
# -*- coding: utf-8 -*-

import json

def updateVar(name, value):
    if name not in indigo.variables:
        indigo.variable.create(name, value=value)
    else:
        indigo.variable.updateValue(name, value)

class Plugin(indigo.PluginBase):
    def __init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs):
        indigo.PluginBase.__init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs)

        self.pluginId = pluginId

        self.testTriggeraction = None
        self.testTrigger = None
        self.customExit = None
        self.customEnter = None
        self.customAction = None
        self.customLocation = None
        self.customSender = None
        self.custom = None
        self.createVar = None
        self.geofency = None
        self.geohopper = None
        self.geofancy = None
        self.beecon = None
        self.createDevice = None
        self.debug = None
        self.deviceList = {}

        self.events = dict()
        self.events["stateChange"] = dict()
        self.events["statePresent"] = dict()
        self.events["stateAbsent"] = dict()

        self.reflector_api_key = None

    def startup(self):
        self.loadPluginPrefs()
        self.logger.debug("Startup called")

    def deviceCreated(self, device):
        self.logger.debug(device.name + f"Created device of type \"{device.deviceTypeId}\"")
        self.deviceList[device.id] = {'ref': device, 'name': device.name, 'address': device.address.lower()}

    def deviceStartComm(self, device):
        self.logger.debug(f"{device.name }: Starting device")
        if device.deviceTypeId == 'userLocation':
            self.logger.error(f"Device {device.name} needs to be deleted and recreated.")
        else:
            self.deviceList[device.id] = {'ref': device, 'name': device.name, 'address': device.address.lower()}

    def deviceStopComm(self, device):
        self.logger.debug(f"{device.name}: Stopping device")
        if device.deviceTypeId == u'beacon':
            del self.deviceList[device.id]

    def shutdown(self):
        self.logger.debug(u"Shutdown called")

    def triggerStartProcessing(self, trigger):
        self.logger.debug(f"Start processing trigger {trigger.name}")
        self.events[trigger.pluginTypeId][trigger.id] = trigger

    def triggerStopProcessing(self, trigger):
        self.logger.debug(f"Stop processing trigger {trigger.name}")
        if trigger.pluginTypeId in self.events:
            if trigger.id in self.events[trigger.pluginTypeId]:
                del self.events[trigger.pluginTypeId][trigger.id]

    def actionControlSensor(self, action, device):
        self.logger.debug(f"Manual sensor state change request: {device.name}")
        if device.pluginProps.get('AllowOnStateChange', False):
            if action.sensorAction == indigo.kSensorAction.TurnOn:
                device.updateStateOnServer("onOffState", True)
                device.updateStateImageOnServer(indigo.kStateImageSel.MotionSensorTripped)
            elif action.sensorAction == indigo.kSensorAction.TurnOff:
                device.updateStateOnServer("onOffState", False)
                device.updateStateImageOnServer(indigo.kStateImageSel.MotionSensor)
            elif action.sensorAction == indigo.kSensorAction.Toggle:
                device.updateStateOnServer("onOffState", not device.onState)
                if device.onState:
                    device.updateStateImageOnServer(indigo.kStateImageSel.MotionSensorTripped)
                else:
                    device.updateStateImageOnServer(indigo.kStateImageSel.MotionSensor)
        else:
            self.logger.debug("ignored request (sensor is read-only)")

    def validatePrefsConfigUi(self, valuesDict):
        self.logger.debug(u"validating Prefs called")
        errorMsgDict = indigo.Dict()

        if valuesDict["reflector_api_key"] == "":
            errorMsgDict['reflector_api_key'] = "Reflector API Key is required"

        if valuesDict['custom']:
            if valuesDict['customSender'] == "":
                errorMsgDict['customSender'] = u"Sender field can't be empty"
            if valuesDict['customLocation'] == "":
                errorMsgDict['customLocation'] = "Location field can't be empty"
            if valuesDict['customAction'] == "":
                errorMsgDict['customAction'] = "Action field can't be empty"
            if valuesDict['customEnter'] == "":
                errorMsgDict['customEnter'] = "Enter field can't be empty"
            if valuesDict['customExit'] == "":
                errorMsgDict['customExit'] = "Exit field can't be empty"
            if valuesDict['customEnter'] == valuesDict['customExit']:
                errorMsgDict['customExit'] = "Enter and Exit fields can't have same value"
            if valuesDict['customSender'] == valuesDict['customLocation']:
                errorMsgDict['customLocation'] = "Sender and Location fields can't have same value"

        if len(errorMsgDict) > 0:
            return False, valuesDict, errorMsgDict
        return True, valuesDict

    def closedPrefsConfigUi(self, valuesDict, UserCancelled):
        if UserCancelled:
            return
        indigo.server.log("Preferences were updated.")
        self.loadPluginPrefs()

    def loadPluginPrefs(self):
        self.logger.debug(u"loadpluginPrefs called")
        self.debug = self.pluginPrefs.get('debugEnabled', False)
        self.reflector_api_key = self.pluginPrefs.get("reflector_api_key", None)

        self.createDevice = self.pluginPrefs.get('createDevice', True)
        self.beecon = self.pluginPrefs.get('beecon', True)
        self.geofancy = self.pluginPrefs.get('geofancy', True)
        self.geohopper = self.pluginPrefs.get('geohopper', True)
        self.geofency = self.pluginPrefs.get('geofency', True)
        self.createVar = self.pluginPrefs.get('createVar', False)
        self.custom = self.pluginPrefs.get('custom', False)
        self.customSender = self.pluginPrefs.get('customSender', 'sender')
        self.customLocation = self.pluginPrefs.get('customLocation', 'location')
        self.customAction = self.pluginPrefs.get('customAction', 'action')
        self.customEnter = self.pluginPrefs.get('customEnter', 'enter')
        self.customExit = self.pluginPrefs.get('customExit', 'exit')
        self.testTrigger = self.pluginPrefs.get('testTrigger', False)
        self.testTriggeraction = self.pluginPrefs.get('testTriggeraction', 'toggle')

    # Test here to see if Reflector webhook is available, get reflector name, etc.
        if not self.reflector_api_key:
            self.logger.warning("Unable to set up webhooks - no reflector API key")
        else:
            self.logger.info(f"Reflector webhook_url: {indigo.server.getReflectorURL()}/message/{self.pluginId}/webhook?api_key={self.reflector_api_key}")

    def deviceUpdate(self, device, deviceAddress, event):
        self.logger.debug("deviceUpdate called")

        if self.createVar:
            updateVar("Beacon_deviceID", str(device.id))
            updateVar("Beacon_name", deviceAddress.split('@@')[0])
            updateVar("Beacon_location", deviceAddress.split('@@')[1])

        if event == "LocationEnter" or event == "enter" or event == "1" or event == self.customEnter:
            indigo.server.log(f"Enter location notification received from sender/location {deviceAddress}")
            device.updateStateOnServer("onOffState", True)
            device.updateStateImageOnServer(indigo.kStateImageSel.MotionSensorTripped)
            self.triggerEvent("statePresent", deviceAddress)
        elif event == "LocationExit" or event == "exit" or event == "0" or event == self.customExit:
            indigo.server.log(f"Exit location notification received from sender/location {deviceAddress}")
            device.updateStateOnServer("onOffState", False)
            device.updateStateImageOnServer(indigo.kStateImageSel.MotionSensor)
            self.triggerEvent("stateAbsent", deviceAddress)
        elif event == "LocationTest" or event == "test":
            indigo.server.log(f"Test location notification received from sender/location {deviceAddress}")
            if self.testTrigger:
                indigo.server.log(f"Trigger action on test is enabled, triggeraction: {self.testTrigger}")
                if self.testTriggeraction == "enter":
                    device.updateStateOnServer("onOffState", True)
                    device.updateStateImageOnServer(indigo.kStateImageSel.MotionSensorTripped)
                elif self.testTriggeraction == "exit":
                    device.updateStateOnServer("onOffState", False)
                    device.updateStateImageOnServer(indigo.kStateImageSel.MotionSensor)
                elif self.testTriggeraction == "toggle":
                    device.updateStateOnServer("onOffState", not device.onState)
                    if device.onState:
                        device.updateStateImageOnServer(indigo.kStateImageSel.MotionSensorTripped)
                    else:
                        device.updateStateImageOnServer(indigo.kStateImageSel.MotionSensor)
        self.triggerEvent("stateChange", deviceAddress)

    def triggerEvent(self, eventType, deviceAddress):
        self.logger.debug("triggerEvent called")
        for trigger in self.events[eventType]:
            if self.events[eventType][trigger].pluginProps["manualAddress"]:
                indigo.trigger.execute(trigger)
            elif fnmatch.fnmatch(deviceAddress.lower(), self.events[eventType][trigger].pluginProps["deviceAddress"].lower()):
                indigo.trigger.execute(trigger)

    def deviceCreate(self, sender, location):
        self.logger.debug("deviceCreate called")
        deviceName = f"{sender}@@{location}"
        device = indigo.device.create(address=deviceName, deviceTypeId="beacon", name=deviceName, protocol=indigo.kProtocol.Plugin)
        self.deviceList[device.id] = {'ref': device, 'name': device.name, 'address': device.address.lower()}
        self.logger.debug(f"Created new device, {deviceName}")
        device.updateStateOnServer("onOffState", False)
        device.updateStateImageOnServer(indigo.kStateImageSel.MotionSensor)
        return device.id

    def parseResult(self, sender, location, event):
        self.logger.debug(f"parseResult called, sender: {sender}, location: {location}, event: {event}")
        deviceAddress = f"{sender.lower()}@@{location.lower()}"
        foundDevice = False
        if self.deviceList:
            for b in self.deviceList:
                if self.deviceList[b]['address'] == deviceAddress:
                    self.logger.debug(f"Found userLocation device: {self.deviceList[b]['name']}")
                    self.deviceUpdate(self.deviceList[b]['ref'], deviceAddress, event)
                    foundDevice = True
        if not foundDevice:
            self.logger.warning(f"Received {event} from {deviceAddress} but no corresponding device exists")
            if self.createDevice:
                newdev = self.deviceCreate(sender, location)
                self.deviceUpdate(self.deviceList[newdev]['ref'], deviceAddress, event)

    def reflector_handler(self, action, dev=None, callerWaitingForResult=None):
        self.logger.debug(f"reflector_handler: {action.props}")
        self.process_message(action.props)
        return "200"

    def process_message(self, action_props):
        foundDevice = False

        try:
            ctype = action_props['headers']['Content-Type']
            uagent = action_props['headers']['User-Agent']
            self.logger.debug(f"User-agent: {uagent}, Content-type: {ctype}")

            # Custom
            if self.custom and (ctype == 'application/x-www-form-urlencoded; charset=utf-8'):
                p = {}
                for key, value in action_props['body_params'].items():
                    p.update({key: value})
                if all((name in p) for name in (self.customSender, self.customLocation, self.customAction)):
                    self.logger.debug(u"Recognised Custom")
                    if (p[self.customAction] == self.customEnter) or (p[self.customAction] == self.customExit):
                        self.parseResult(p[self.customSender], p[self.customLocation], p[self.customAction])
                    else:
                        self.logger.error("Received Custom data, but value of Action parameter wasn't recognised")
                    return

            # Locative or Geofancy
            if ('Geofancy' in uagent) or ('Locative' in uagent):
                self.logger.debug("Recognised Locative/Geofancy")
                if self.geofancy:
                    if ctype == 'application/x-www-form-urlencoded; charset=utf-8':
                        p = {}
                        for key, value in action_props['body_params'].items():
                            p.update({key: value})
                        if all((name in p) for name in ('device', 'id', 'trigger')):
                            self.parseResult(p["device"], p["id"], p["trigger"])
                        else:
                            self.logger.error("Received Locative/Geofancy data, but one or more parameters are missing")
                    else:
                        self.logger.error(f"Recognised Locative/Geofancy, but received data was wrong content-type: {ctype}")
                else:
                    self.logger.warning("Received Locative/Geofancy data, but Locative/Geofancy is disabled in plugin config")

            # Geofency
            elif 'Geofency' in uagent:
                self.logger.debug("Recognised Geofency")
                if self.geofency:
                    if ctype == 'application/x-www-form-urlencoded':
                        p = {}
                        for key, value in action_props['body_params'].items():
                            p.update({key: value})
                        if all((name in p) for name in ('name', 'entry', 'device')):
                            self.parseResult(p["device"], p["name"], p["entry"])
                        else:
                            self.logger.error(u"Received Geofency data, but one or more parameters are missing")
                    elif ctype == 'application/json':
                        p = json.loads(action_props['request_body'])
                        if all((name in p) for name in ('name', 'entry', 'device')):
                            self.parseResult(p["device"], p["name"], p["entry"])
                        else:
                            self.logger.error(u"Received Geofency data, but one or more parameters are missing")
                    else:
                        self.logger.error(f"Recognised Geofency, but received data was wrong content-type: {ctype}")
                else:
                    self.logger.warning(u"Received Geofency data, but Geofency is disabled in plugin config")

            # Beecon
            elif 'Beecon' in uagent:
                self.logger.debug("Recognised Beecon")
                if self.beecon:
                    p = json.loads(action_props['request_body'])
                    if all((name in p) for name in ('region', 'action')):
                        self.parseResult("Beecon", p["region"], p["action"])
                    else:
                        self.logger.error(u"Received Beecon data, but one or more parameters are missing")
                else:
                    self.logger.warning(u"Received Beecon data, but Beecon is disabled in plugin config")

            # Geohopper
            elif ctype == 'application/json':
                self.logger.debug(u"Received JSON data (possible Geohopper)")
                if self.geohopper:
                    p = json.loads(action_props['request_body'])
                    if all((name in p) for name in ('sender', 'location', 'event')):
                        self.parseResult(p["sender"], p["location"], p["event"])
                    else:
                        self.logger.error(u"Received Geohopper data, but one or more parameters are missing")
                else:
                    self.logger.warning(u"Received Geohopper data, but Geohopper is disabled in plugin config")
            else:
                self.logger.error(f"Didn't recognise received data. (User-agent: {uagent}, Content-type: {ctype})")
        except Exception as e:
            self.logger.error(f"Exception: {e}", exc_info=True)
            pass

