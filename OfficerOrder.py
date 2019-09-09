class OfficerOrder:
    def __init__(self, officers=[], filePath=None):
        self.officers = officers
        if filePath is not None:
            self.loadFromFile(filePath)

    def nextOfficer(self, currentOfficers):
        officersAtThisStep = {}
        for stepNumber in range(len(self.officers)):
            officerId = self.officers[stepNumber] #the officerId to be built according to this step
            levelToGet = officersAtThisStep.get(officerId, 0) + 1  #the level it should be after getting it
            officersAtThisStep[officerId] = levelToGet
            currentLevel = currentOfficers.get(officerId, 0)
            if levelToBuild > currentLevel:
                return officerId
        return None

    def loadFromFile(self, filePath):
        self.officers = []
        with open(filePath) as file:
            l = file.readline()
            while l != "":
                l = l.replace("\n", "")
                if len(l) and l[0] != "#":
                    if not ":" in l:
                        l += ":1"
                    id, times = l.split(":")
                    for i in range(times):
                        self.officers.append(int(id))
                l = file.readline()
