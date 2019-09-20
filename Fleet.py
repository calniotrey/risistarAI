import time
from Request import Request

class Fleet:
    attackCode     = 1
    transportCode  = 3
    deployCode     = 4
    stationCode    = 5
    spyCode        = 6
    colonizeCode   = 7
    expeditionCode = 15

    def __init__(self, player, id, ships, origin, target, eta, type, isGoing):
        self.player = player
        self.id = id
        self.ships = ships
        self.origin = origin
        self.target = target
        self.eta = eta
        self.isGoing = isGoing #either is going to target, or is coming back
        self.type = type
        self.isHostile = False
        self.firstSpotted = time.time()

    def isCombat(self):
        return self.isAttack() or self.isDestroy()

    def isAttack(self):
        return self.type == "attack"

    def isDestroy(self):
        return self.type == "destroy"

    def isSpy(self):
        return self.type == "espionage" or self.type == "ownespionage"

    def isHostileSpy(self):
        return self.type == "espionage"

    def isOwnSpy(self):
        return self.type == "ownespionage"

    def isExpedition(self):
        return self.target[2] == 16 or self.origin[2] == 16 #ongoing or coming back

    def sendBack(self): #no check if the fleet is ours
        sendBackRequest = Request(self.player.ia.sendBackFleetPage, {"fleetID": self.id})
        self.player.ia.execRequest(sendBackRequest)
