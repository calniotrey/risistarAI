import os.path

class Config:
    def __init__(self):
        self.domain = None
        self.activateAutoBuild = None
        self.activateAutoFleetScan = None
        self.activateAutoEvasion = None
        self.robotRatio = None
        self.robotStartingLevel = None
        self.minimumTimeBetweenScans = None
        self.randomAdditionnalTimeBetweenScans = None
        self.escapeTarget = None

    def load():
        if os.path.isfile("config.txt"):
            return Config.loadFromFile("config.txt")
        return Config.loadFromFile("defaultConfig.txt")


    def loadFromFile(filePath):
        config = Config()
        file = open(filePath)
        l = file.readline()
        while l != "":
            l = l.replace("\n", "")
            if len(l) and l[0] != "#":
                s = l.split("=")
                key = s[0].replace(" ", "")
                value = s[1]
                if key == "domain":
                    config.domain = value
                elif key == "activateAutoBuild":
                    config.activateAutoBuild = value == "True"
                elif key == "activateAutoFleetScan":
                    config.activateAutoFleetScan = value == "True"
                elif key == "activateAutoEvasion":
                    config.activateAutoEvasion = value == "True"
                elif key == "robotRatio":
                    config.robotRatio = int(value)
                elif key == "robotStartingLevel":
                    config.robotStartingLevel = int(value)
                elif key == "minimumTimeBetweenScans":
                    config.minimumTimeBetweenScans = int(value)
                elif key == "randomAdditionnalTimeBetweenScans":
                    config.randomAdditionnalTimeBetweenScans = int(value)
                elif key == "escapeTarget":
                    config.escapeTarget = [int(x) for x in value.split(":")]
            l = file.readline()
        file.close()
        return config

    def getError(self):
        if None in self.__dict__.values():
            return "Some settings aren't set !"
        if self.activateAutoEvasion and not self.activateAutoFleetScan:
            return "Auto evasion is activated but not auto fleet scan !"
        return None
