from PickOrder import PickOrder

class BuildOrder(PickOrder):
    def __init__(self, name, list=[], filePath=None):
        super().__init__(list, filePath)
        self.name = name

    def nextBuilding(self, planet):
        idToItem = lambda buildingId: planet.buildingById(buildingId)
        return self.nextItem(idToItem)
