import time
from tasks.Task import Task
from tasks.PlanningTask import PlanningTask
from UtilitiesFunctions import log

class BuildingTask(Task):
    def __init__(self, t, bat):
        self.t = t
        self.bat = bat
        self.prio = Task.lowPrio

    def execute(self):
        req = self.bat.upgrade()
        self.bat.planet.scanUsingRequest(req)
        if self.bat.planet.upgradingEnd == 0: #the building wasn't upgraded
            log(self.bat.planet, "Re-planning building")
            newTask = PlanningTask(time.time(), self.bat.planet)
            self.bat.planet.player.ia.addTask(newTask)
        else:
            log(self.bat.planet, "Building " + self.bat.type + " to level " + str(self.bat.level + 1) + " in " + str(self.bat.upgradeTime))
            self.bat.planet.player.ia.addTask(PlanningTask(time.time() + self.bat.upgradeTime, self.bat.planet))
