from Request import Request

class Building:

    def __init__(self, type, id, planet, level=0):
        self.type = type
        self.level = level
        self.planet = planet
        self.id = id
        self.upgradeTime = None
        self.upgradeCost = None

    def upgradable(self, ressources):
        for i in range(0,3):
            if self.upgradeCost[i] > ressources[i]:
                return False
        return True

    def upgrade(self):
        if self.id != None:
            payload = {'cmd': 'insert', 'building': self.id}
            reqB = Request(self.planet.player.ia.buildingPage + "&cp=" + self.planet.id, payload)
            self.planet.player.ia.execRequest(reqB)
            return reqB
