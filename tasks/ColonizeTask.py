import time
from Fleet import Fleet
from tasks.Task import Task
from UtilitiesFunctions import log

class ColonizeTask(Task):
    def __init__(self, t, player):
        self.t = t
        self.player = player
        self.prio = Task.lowPrio

    def execute(self):
        log(None, "Checking if colonization is possible")
        if self.player.getMaximumNumberOfPlanets() > self.player.getActualNumberOfPlanets():
            # This assures that tech is enough
            # We just need to get a planet with a colonization ship or a shipyard 4
            self.player.scanOwnShips()
            scannedSystem = [] # We don't scan a scanned system
            stop = False
            for planet in self.player.planets:
                if not stop and planet.ships.get(208, 0) >= 1:
                    if [planet.pos[0], planet.pos[1]] in scannedSystem:
                        location = planet.getColonizationTarget(useLastKnownSystem=True)
                    else:
                        location = planet.getColonizationTarget()
                        scannedSystem.append([planet.pos[0], planet.pos[1]])
                    if location is not None:
                        stop = True
                        destination = [planet.pos[0], planet.pos[1], location, 1]
                        planet.sendFleet(destination, Fleet.colonizeCode, {208:1}, [0, 0, 0], allRessources=True)
            if not stop: #ie no ship to send to colonize
                log(None, "No colonization launched, trying to build a colony ship")
                for planet in self.player.planets:
                    canBuild = planet.buildingLevelById(21) >= 4 and planet.metal >= 10000 and planet.crystal >= 20000 and planet.deut >= 11000
                    if not stop and planet.ships.get(208, 0) == 0 and canBuild:
                        if [planet.pos[0], planet.pos[1]] in scannedSystem:
                            location = planet.getColonizationTarget(useLastKnownSystem=True)
                        else:
                            location = planet.getColonizationTarget()
                            scannedSystem.append([planet.pos[0], planet.pos[1]])
                        spacePort = planet.buildingById(21)
                        if location is not None:
                            stop = True
                            planet.buildShips({208:1})
                            log(planet, "Started construction of colony ship")
                            timeToWait = 30000/14/(1 + planet.buildingLevelById(21))/(2**planet.buildingLevelById(15)) + 5
                            # The 14 is 2 * universe speed, the + 5 is just a security, could be 1
                            newTask = ColonizeTask(time.time() + timeToWait, self.player)
                            self.player.ia.addTask(newTask)
            if not stop:
                log(None, "Can't build any colony ships in a system with a colonizable planet")
