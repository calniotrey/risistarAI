import time
from tasks.Task import Task
from UtilitiesFunctions import log

class PlanningTask(Task):
    def __init__(self, t, planet):
        self.t = t
        self.planet = planet
        self.prio = Task.lowPrio

    def execute(self):
        log(self.planet, "Scanning planet")
        self.planet.scan()
        if self.planet.sizeMax is None:
            log(self.planet, "Scanning planet size")
            self.planet.getSize()
        log(self.planet, "Done scanning planet " + self.planet.getNameWithSize())
        if self.planet.upgradingEnd: #if a building is currently being build
            log(self.planet, "Waiting for a building to end in " + str(self.planet.upgradingEnd - time.time()))
            newTask = PlanningTask(self.planet.upgradingEnd, self.planet)
            self.planet.player.ia.addTask(newTask)
        else:
            if self.planet.canBuildSolarSatellites():
                log(self.planet, "A solar satellite can be constructed")
                self.planet.buildShips({212:1})
                self.planet.getShipQueueTime()
                log(self.planet, "Checking new building task in " + str(self.planet.shipQueueTime))
                newTask = PlanningTask(time.time() + self.planet.shipQueueTime, self.planet)
                self.planet.player.ia.addTask(newTask)
            elif self.planet.sizeUsed < self.planet.sizeMax:
                log(self.planet, "Planning building")
                newTask = self.planet.planBuilding()
                if newTask is not None:
                    log(self.planet, "Done planning building")
                    log(self.planet, "Planning to build a " + newTask.bat.type + " to level " + str(newTask.bat.level + 1) + " in " + str(newTask.t - time.time()))
            else:
                log(self.planet, "Planet filled ! Retrying in 10 minutes")
                newTask = PlanningTask(time.time() + 600, self.planet)
                self.planet.player.ia.addTask(newTask)
