import os.path

class Config:
    def __init__(self):
        self.domain = None
        self.userAgent = None
        self.activateAutoBuild = None
        self.activateCustomBuildOrders = None
        self.activateAutoResearch = None
        self.activateAutoFleetScan = None
        self.activateDefenderDiscordPing = None
        self.activateAutoEvasion = None
        self.activateAutoExpedition = None
        self.activateAutoColonization = None
        self.activatePickingOfficers = None
        self.robotRatio = None
        self.robotStartingLevel = None
        self.customBuildOrdersDirectoryName = None
        self.customBuildOrdersPairingFile = None
        self.techsPickingOrderFile = None
        self.minimumTimeBetweenScans = None
        self.randomAdditionnalTimeBetweenScans = None
        self.webhookUrl = None
        self.idToPing = None
        self.customAttackNotificationMessage = None
        self.escapeTarget = None
        self.minimumSpottingTime = None
        self.launchExpeditionSeparately = None
        self.officersPickingOrderFile = None
        self.watchdogDelay = None
        self.watchdogExceptionDelay = None
        self.watchdogEarlyDelay = None
        self.watchdogWakeDuration = None

    def load():
        config = Config()
        config.loadFromFile("defaultConfig.txt")
        if os.path.isfile("config.txt"):
            config.loadFromFile("config.txt")
        return config

    def loadFromFile(self, filePath):
        with open(filePath) as file:
            l = file.readline()
            while l != "":
                l = l.replace("\n", "")
                if len(l) and l[0] != "#":
                    s = l.split("=")
                    key = s[0].replace(" ", "")
                    value = s[1]
                    if key == "domain":
                        self.domain = value
                    elif key == "userAgent":
                        self.userAgent = value
                    elif key == "activateAutoBuild":
                        self.activateAutoBuild = value == "True"
                    elif key == "activateCustomBuildOrders":
                        self.activateCustomBuildOrders = value == "True"
                    elif key == "activateAutoResearch":
                        self.activateAutoResearch = value == "True"
                    elif key == "activateAutoFleetScan":
                        self.activateAutoFleetScan = value == "True"
                    elif key == "activateDefenderDiscordPing":
                        self.activateDefenderDiscordPing = value == "True"
                    elif key == "activateAutoEvasion":
                        self.activateAutoEvasion = value == "True"
                    elif key == "activateAutoExpedition":
                        self.activateAutoExpedition = value == "True"
                    elif key == "activateAutoColonization":
                        self.activateAutoColonization = value == "True"
                    elif key == "activatePickingOfficers":
                        self.activatePickingOfficers = value == "True"
                    elif key == "robotRatio":
                        self.robotRatio = int(value)
                    elif key == "robotStartingLevel":
                        self.robotStartingLevel = int(value)
                    elif key == "customBuildOrdersDirectoryName":
                        self.customBuildOrdersDirectoryName = value
                    elif key == "customBuildOrdersPairingFile":
                        self.customBuildOrdersPairingFile = value
                    elif key == "techsPickingOrderFile":
                        self.techsPickingOrderFile = value
                    elif key == "minimumTimeBetweenScans":
                        self.minimumTimeBetweenScans = int(value)
                    elif key == "randomAdditionnalTimeBetweenScans":
                        self.randomAdditionnalTimeBetweenScans = int(value)
                    elif key == "webhookUrl":
                        self.webhookUrl = value
                    elif key == "idToPing":
                        self.idToPing = value
                    elif key == "customAttackNotificationMessage":
                        self.customAttackNotificationMessage = value
                    elif key == "escapeTarget":
                        self.escapeTarget = [int(x) for x in value.split(":")]
                    elif key == "minimumSpottingTime":
                        self.minimumSpottingTime = int(value)
                    elif key == "officersPickingOrderFile":
                        self.officersPickingOrderFile = value
                    elif key == "launchExpeditionSeparately":
                        self.launchExpeditionSeparately = value == "True"
                    elif key == "watchdogDelay":
                        self.watchdogDelay = int(value)
                    elif key == "watchdogExceptionDelay":
                        self.watchdogExceptionDelay = int(value)
                    elif key == "watchdogEarlyDelay":
                        self.watchdogEarlyDelay = int(value)
                    elif key == "watchdogWakeDuration":
                        self.watchdogWakeDuration = int(value)
                l = file.readline()

    def getError(self):
        if None in self.__dict__.values():
            return "Some settings aren't set !"
        if self.activateCustomBuildOrders and not self.activateAutoBuild:
            return "Custom build orders is activated but not auto build !"
        if self.activateCustomBuildOrders and self.customBuildOrdersDirectoryName is None:
            return "Custom build orders is activated but the build orders directory isn't specified !"
        if self.activateCustomBuildOrders and self.customBuildOrdersPairingFile is None:
            return "Custom build orders is activated but the build orders pairing file isn't specified !"
        if self.activateAutoEvasion and not self.activateAutoFleetScan:
            return "Auto evasion is activated but not auto fleet scan !"
        if self.activateAutoExpedition and not self.activateAutoFleetScan:
            return "Auto expedition is activated but not auto fleet scan !"
        if self.activateDefenderDiscordPing and not self.activateAutoFleetScan:
            return "Defender ping is activated but not auto fleet scan !"
        if self.activateDefenderDiscordPing and self.webhookUrl == "None":
            return "Defender ping is activated but the webhook url isn't configurated !"
        if self.activateDefenderDiscordPing and self.idToPing == "None":
            return "Defender ping is activated but the user id to ping isn't configurated !"
        if self.activatePickingOfficers and self.officersPickingOrderFile is None:
            return "Officer picking is activated but the order isn't configurated !"
        if self.watchdogDelay is None:
            return "watchdogDelay isn't defined"
        if self.watchdogDelay <= 0:
            return "watchdogDelay should be strictly positive (for example 1800 ie 30 minutes)"
        if self.watchdogExceptionDelay is None:
            return "watchdogExceptionDelay isn't defined (in doubt, put it at 0)"
        if self.watchdogEarlyDelay is None:
            return "watchdogEarlyDelay isn't defined (in doubt, put it at 0)"
        if self.watchdogWakeDuration is None:
            return "watchdogWakeDuration isn't defined (in doubt, put it at 5)"
        return None
