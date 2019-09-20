import random
import time
from tasks.Task import Task
from tasks.SendExpeditionTask import SendExpeditionTask
from Fleet import Fleet
from UtilitiesFunctions import log

class ScanFleetsTask(Task):
    def __init__(self, t, player, randomAdditionnalWait=None):
        if randomAdditionnalWait is None:
            randomAdditionnalWait = player.ia.config.randomAdditionnalTimeBetweenScans
        self.t = t + random.random() * randomAdditionnalWait
        self.player = player
        self.prio = Task.middlePrio

    def execute(self):
        ia = self.player.ia #just to make the lines smaller
        self.player.getFleets()
        log(None, "Scanned fleets")
        ennemyFleetInc = False
        for fleet in self.player.fleets.values():
            targetPlanet = self.player.getOwnPlanetByPosition(fleet.target)
            if fleet.isCombat() and targetPlanet is not None and fleet.isGoing: #if we are getting attacked
                log(None, "HOSTILE FLEET targeting " + targetPlanet.name + " in " + str(int(fleet.eta - time.time())))
                ennemyFleetInc = True
                if ia.config.activateDefenderDiscordPing:
                    try:
                        message = ia.config.customAttackNotificationMessage
                        message = message.replace("{targetPlanet.name}", targetPlanet.name)
                        message = message.replace("{targetPlanet.position}", targetPlanet.getPosAsString())
                        message = message.replace("{fleet.ttd}", str(int(fleet.eta - time.time())))
                        ia.pingUser(message)
                    except:
                        log(targetPlanet, "Error while pinging Discord user. Make sure the webhook is correct.")
                minimumTimeWindowToLaunch = 2 * ia.config.minimumTimeBetweenScans + ia.config.randomAdditionnalTimeBetweenScans
                shouldEvade = (fleet.eta - time.time()) < minimumTimeWindowToLaunch
                shouldEvade = shouldEvade and ia.config.activateAutoEvasion
                shouldEvade = shouldEvade and (time.time() - fleet.firstSpotted) >= ia.config.minimumSpottingTime
                if shouldEvade:
                    targetPlanet.scanShips()
                    log(None, "Simulating combat")
                    rapport = self.player.ia.simulateCombat(fleet.ships, targetPlanet.ships) #TODO add defense
                    if rapport.combatResult == 1 or (rapport.combatResult == 0 and not fleet.isDestroy()):
                        #if we (the defender) loose, or if it's a tie and it's not a moon destruction mission
                        log(None, "The incoming battle isn't in our favor, initiating evasion")
                        if targetPlanet.ships: #if there are some ships to send
                            try:
                                targetPlanet.sendFleet(ia.config.escapeTarget, Fleet.transportCode, targetPlanet.ships, [0, 0, 0], speed=1, allRessources=True)
                            except:
                                log(targetPlanet, "Error while sending the fleet for evasion")
                        targetPlanet.scanRessourcesUsingRequest(self.player.lastRequest)
                        gt = min(targetPlanet.metal//6000, targetPlanet.crystal//6000)
                        targetPlanet.buildShips({203:gt})
                        targetPlanet.scanRessourcesUsingRequest(self.player.lastRequest)
                        pt = min(targetPlanet.metal//2000, targetPlanet.crystal//2000)
                        targetPlanet.buildShips({202:pt})
                        targetPlanet.scanRessourcesUsingRequest(self.player.lastRequest)
                        lle = min(targetPlanet.metal//1500, targetPlanet.crystal//500)
                        targetPlanet.buildDefenses({402:lle})
                        targetPlanet.scanRessourcesUsingRequest(self.player.lastRequest)
                        lm = targetPlanet.metal//2000
                        targetPlanet.buildDefenses({401:lm})
                    else:
                        log(None, "The incoming battle is in our favor. Battlestations!")
        try:
            if not ennemyFleetInc:
                for fleet in self.player.fleets.values():
                    if fleet.target == ia.config.escapeTarget:
                        fleet.sendBack()
        except:
            log(None, "Error while sending back fleet from evasion")
        if ia.config.activateAutoExpedition:
            numberOfExpeditionsToLaunch = self.player.getMaximumNumberOfExpeditions() - self.player.getActualNumberOfExpeditions()
            if ia.config.launchExpeditionSeparately:
                numberOfExpeditionsToLaunch = min(1, numberOfExpeditionsToLaunch)
            for i in range(numberOfExpeditionsToLaunch):
                newExpeditionTask = SendExpeditionTask(time.time(), self.player)
                ia.addTask(newExpeditionTask)
        newTask = ScanFleetsTask(time.time() + ia.config.minimumTimeBetweenScans, self.player)
        ia.addTask(newTask)
