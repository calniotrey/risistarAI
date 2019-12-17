from PickOrder import PickOrder

class TechsPickingOrder(PickOrder):

    def nextTech(self, currentTechs):
        idToItem = lambda techId: currentTechs.get(techId, None)
        return self.nextItem(idToItem)
