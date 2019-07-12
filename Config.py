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
        self.minimumSpottingTime = None

    def load():
        config = Config()
        config.loadFromFile("defaultConfig.txt")
        if os.path.isfile("config.txt"):
            config.loadFromFile("config.txt")
        return config


    def loadFromFile(self, filePath):
        file = open(filePath)
        l = file.readline()
        while l != "":
            l = l.replace("\n", "")
            if len(l) and l[0] != "#":
                s = l.split("=")
                key = s[0].replace(" ", "")
                value = s[1]
                if key == "domain":
                    self.domain = value
                elif key == "activateAutoBuild":
                    self.activateAutoBuild = value == "True"
                elif key == "activateAutoFleetScan":
                    self.activateAutoFleetScan = value == "True"
                elif key == "activateAutoEvasion":
                    self.activateAutoEvasion = value == "True"
                elif key == "robotRatio":
                    self.robotRatio = int(value)
                elif key == "robotStartingLevel":
                    self.robotStartingLevel = int(value)
                elif key == "minimumTimeBetweenScans":
                    self.minimumTimeBetweenScans = int(value)
                elif key == "randomAdditionnalTimeBetweenScans":
                    self.randomAdditionnalTimeBetweenScans = int(value)
                elif key == "escapeTarget":
                    self.escapeTarget = [int(x) for x in value.split(":")]
                elif key == "minimumSpottingTime":
                    self.minimumSpottingTime = int(value)
            l = file.readline()
        file.close()

    def getError(self):
        if None in self.__dict__.values():
            return "Some settings aren't set !"
        if self.activateAutoEvasion and not self.activateAutoFleetScan:
            return "Auto evasion is activated but not auto fleet scan !"
        return None
