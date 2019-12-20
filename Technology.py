from Request import Request
from UtilitiesFunctions import log

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

    def requirementsMet(self, planet):
        labLevel = planet.buildingLevelById(31)
        if self.id == 106:
            return labLevel >= 3
        elif self.id == 108:
            return labLevel >= 1
        elif self.id == 109:
            return labLevel >= 4
        elif self.id == 110:
            return labLevel >= 6 and self.player.getTechLevel(113) >= 3
        elif self.id == 111:
            return labLevel >= 2
        elif self.id == 113:
            return labLevel >= 1
        elif self.id == 114:
            return labLevel >= 7 and self.player.getTechLevel(113) >= 5 and self.player.getTechLevel(110) >= 5
        elif self.id == 115:
            return labLevel >= 1 and self.player.getTechLevel(113) >= 1
        elif self.id == 117:
            return labLevel >= 2 and self.player.getTechLevel(113) >= 1
        elif self.id == 118:
            return labLevel >= 7 and self.player.getTechLevel(114) >= 3
        elif self.id == 120:
            return labLevel >= 1 and self.player.getTechLevel(113) >= 2
        elif self.id == 121:
            return labLevel >= 4 and self.player.getTechLevel(113) >= 4 and self.player.getTechLevel(120) >= 5
        elif self.id == 122:
            return labLevel >= 5 and self.player.getTechLevel(113) >= 8 and self.player.getTechLevel(120) >= 10 and self.player.getTechLevel(121) >= 5
        elif self.id == 123:
            return labLevel >= 10 and self.player.getTechLevel(108) >= 8 and self.player.getTechLevel(114) >= 8
        elif self.id == 124:
            return labLevel >= 3 and self.player.getTechLevel(106) >= 3 and self.player.getTechLevel(117) >= 3
        elif self.id == 131:
            return labLevel >= 8 and self.player.getTechLevel(115) >= 5
        elif self.id == 132:
            return labLevel >= 8 and self.player.getTechLevel(115) >= 5
        elif self.id == 133:
            return labLevel >= 8 and self.player.getTechLevel(115) >= 5
        elif self.id == 134:
            return labLevel >= 12 and self.player.getTechLevel(199) >= 1 and self.player.getTechLevel(114) >= 8 and self.player.getTechLevel(123) >= 3
        elif self.id == 199:
            return labLevel >= 12
        log(planet, "ERROR : Technology (id=%i) doesn't have it's requirements in the list. Contact the developper and send the logs" % (self.id))
        return False # Fallback
