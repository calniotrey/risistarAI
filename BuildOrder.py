class BuildOrder:
    def __init__(self, name, buildings=[], filePath=None):
        self.name = name
        self.buildings = buildings
        self.useDefaultBuildPlanWhenEmpty = True
        if filePath is not None:
            self.loadFromFile(filePath)

    def nextBuilding(self, planet):
        buildingsAtThisStep = {}
        for stepNumber in range(len(self.buildings)):
            buildingId = self.buildings[stepNumber] #the buildingId to be built according to this step
            levelToBuild = buildingsAtThisStep.get(buildingId, 0) + 1  #the level it should be after building
            buildingsAtThisStep[buildingId] = levelToBuild
            currentLevel = planet.buildingLevelById(buildingId)
            if levelToBuild > currentLevel:
                return buildingId
        return None

    def loadFromFile(self, filePath):
        self.buildings = []
        with open(filePath) as file:
            l = file.readline()
            startedBuildingsList = False
            while l != "":
                l = l.replace("\n", "")
                if len(l) and l[0] != "#":
                    if not startedBuildingsList:
                        if l == "Buildings:":
                            startedBuildingsList = True
                        else:
                            s = l.split("=")
                            key = s[0].replace(" ", "")
                            value = s[1]
                            if key == "useDefaultBuildPlanWhenEmpty":
                                self.useDefaultBuildPlanWhenEmpty = value == "True"
                            #TODO add more configurations at the beginning of the build order
                    else:
                        self.buildings.append(int(l))
                l = file.readline()
