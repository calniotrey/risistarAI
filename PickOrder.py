from UtilitiesFunctions import is_number

class PickOrder:
    def __init__(self, list=[], filePath=None):
        self.list = list
        self.options = {}
        if filePath is not None:
            self.loadFromFile(filePath)

    def loadFromFile(self, filePath):
        self.list = []
        self.options = {}
        with open(filePath) as file:
            l = file.readline()
            startedOrderList = False
            while l != "":
                l = l.replace("\n", "")
                if len(l) and l[0] != "#":
                    if l[0].isdigit():
                        if not ":" in l:
                            l += ":1"
                        id, times = l.split(":")
                        for i in range(int(times)):
                            self.list.append(int(id))
                    else:
                        s = l.split("=")
                        key = s[0].replace(" ", "")
                        value = s[1]
                        if value == "True" or "False":
                            self.options[key] = value == "True"
                        elif is_number(value):
                            self.options[key] = float(value)
                        else:
                            self.options[key] = value
                l = file.readline()

    def nextItem(self, idToItem):
        itemsAtThisStep = {}
        for stepNumber in range(len(self.list)):
            itemId = self.list[stepNumber] #the itemId to be selected according to this step
            levelToGet = itemsAtThisStep.get(itemId, 0) + 1  #the level it should be after getting it
            itemsAtThisStep[itemId] = levelToGet
            currentItem = idToItem(itemId)
            if currentItem is None or levelToGet > currentItem.level:
                return currentItem
        return None
