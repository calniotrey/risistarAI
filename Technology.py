from Request import Request

class Technology:
    def __init__(self, type, id, player, level=0):
        self.type = type
        self.level = level
        self.player = player
        self.id = id
        self.upgradeTime = None
        self.upgradeCost = None

    def upgradable(self, ressources):
        for i in range(0,3):
            if self.upgradeCost[i] > ressources[i]:
                return False
        return True

    def upgrade(self, planetId):
        if self.id != None:
            payload = {'cmd': 'insert', 'tech': self.id}
            reqB = Request(self.player.ia.researchPage + "&cp=" + str(planetId), payload)
            self.player.ia.execRequest(reqB)
            return reqB

    def getTotalUpgradeCostWeighted(self, weight=[3, 2, 1]):
        """sum of upgradeCost[i]/weight[i]"""
        sum = 0
        for i in range(3):
            sum += self.upgradeCost[i]/weight[i]
        return sum
