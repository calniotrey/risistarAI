from tasks.Task import Task
from Fleet import Fleet
from UtilitiesFunctions import log

class SendExpeditionTask(Task):
    def __init__(self, t, player):
        self.t = t
        self.player = player
        self.prio = Task.lowPrio

    def execute(self):
        log(None, "Planning launch of an expedition")
        self.player.scanOwnShips()
        stop = False
        for planet in self.player.planets:
            if not stop and planet.deut >= 10:
                if planet.ships.get(232, 0) >= 1:
                    planet.sendFleet(planet.pos[0:2] + [16, 1], Fleet.expeditionCode, {232:1}, [0, 0, 0])
                    stop = True
                elif planet.ships.get(203, 0) >= 1:
                    planet.sendFleet(planet.pos[0:2] + [16, 1], Fleet.expeditionCode, {203:1}, [0, 0, 0])
                    stop = True
                elif planet.ships.get(202, 0) >= 1:
                    planet.sendFleet(planet.pos[0:2] + [16, 1], Fleet.expeditionCode, {202:1}, [0, 0, 0])
                    stop = True
                if stop:
                    log(planet, "Launched an expedition!")
        if not stop: #ie no ship to send on any planet
            log(None, "No expedition launched, trying to build a small transporter")
            combustionResearch = self.player.researchs.get(115, None)
            if combustionResearch is not None and combustionResearch.level >= 2:
                for planet in self.player.planets:
                    if not stop and planet.metal >= 2000 and metal.crystal >= 2000 and planet.deut >= 10:
                        spacePort = planet.buildingById(21)
                        if spacePort is not None and spacePort.level >= 2:
                            planet.buildShips({202:1})
                            stop = True
                            log(planet, "Small transporter construction started")
            if not stop:
                log(None, "Can't build any small transporter")
