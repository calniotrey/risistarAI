from Request import Request

class Research:
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

    def upgrade(self):
        if self.id != None:
            payload = {'cmd': 'insert', 'tech': self.id}
            reqB = Request(self.player.ia.researchPage + "&cp=" + str(self.player.ia.config.researchPlanetId), payload)
            self.player.ia.execRequest(reqB)
            return reqB
