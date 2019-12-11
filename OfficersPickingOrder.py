from PickOrder import PickOrder

class OfficersPickingOrder(PickOrder):

    def nextOfficer(self, currentOfficers):
        idToItem = lambda officerId: currentOfficers.get(officerId, None)
        return self.nextItem(idToItem)
