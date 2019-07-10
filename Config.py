import os.path

class Config:
    def __init__(self):
        self.domain = ""
        self.escapeTarget = ""
        self.robotRatio = ""
        self.robotStartingLevel = ""

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
                elif key == "escapeTarget":
                    config.escapeTarget = [int(x) for x in value.split(":")]
                elif key == "robotRatio":
                    config.robotRatio = int(value)
                elif key == "robotStartingLevel":
                    config.robotStartingLevel = int(value)
            l = file.readline()
        file.close()
        return config
