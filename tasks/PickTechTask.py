import time
from Codes import Codes
from tasks.Task import Task
from tasks.ColonizeTask import ColonizeTask
from UtilitiesFunctions import log

class PickTechTask(Task):
    def __init__(self, t, player):
        self.t = t
        self.player = player
        self.prio = Task.lowPrio

    def execute(self):
        self.player.scanTechs()
        if self.player.ia.config.activateAutoColonization:
            # Eventually add a colonization task
            isAlreadyColonizing = False
            for fleet in self.player.fleets.values():
                if not isAlreadyColonizing and fleet.isColony():
                    isAlreadyColonizing = True
            shouldAddTask = not isAlreadyColonizing
            shouldAddTask = shouldAddTask and self.player.getActualNumberOfPlanets() < self.player.getMaximumNumberOfPlanets()
            shouldAddTask = shouldAddTask and not self.player.ia.hasTaskOfType(ColonizeTask)
            if shouldAddTask:
                newTask = ColonizeTask(time.time(), self.player)
                self.player.ia.addTask(newTask)
        if self.player.researchEnd > 0: #If there is already a tech being researched
            log(None, "Waiting for a research to finish in " + str(self.player.researchEnd - time.time()))
            newTask = PickTechTask(self.player.researchEnd + 1, self.player)
            self.player.ia.addTask(newTask)
        else:
            tech, planet = self.player.chooseTechToPick()
            if tech is not None:
                if tech.upgradable([planet.metal, planet.crystal, planet.deut]):
                    req = tech.upgrade(planet.id)
                    self.player.scanTechsUsingRequest(self.player.lastRequest)
                    log(planet, "Researching %s in %s" % (tech.type, str(self.player.researchEnd - time.time())))
                    newTask = PickTechTask(self.player.researchEnd + 1, self.player)
                    self.player.ia.addTask(newTask)
                else:
                    #now we need to know how much to wait
                    log(planet, "Waiting for resources for tech %s" % tech.type)
                    timeToWait = planet.getTimeToWaitForResources(tech.upgradeCost)
                    timeToStart = time.time() + timeToWait
                    newTaskTime = timeToStart
                    if len(planet.upgradingBuildingsId) and planet.upgradingBuildingsId[0][1] < timeToStart:
                        # A building is planned before we can start the research
                        newTaskTime = planet.upgradingBuildingsId[0][1]
                    newTask = PickTechTask(newTaskTime, self.player)
                    self.player.ia.addTask(newTask)
