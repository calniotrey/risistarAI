import random
import time
from tasks.Task import Task
from tasks.SendExpeditionTask import SendExpeditionTask
from Fleet import Fleet
from Request import Request
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
        if ia.config.activateAllianceScan:
            ia.retrieveShrib()
            pseudo, stopScan, nextScan, content = ia.decodeShrib()
            willLead = False
            # if there is currently no one scanning
            willLead = willLead or (pseudo is None)
            # or it is us
            willLead = willLead or (pseudo == self.player.pseudo)
            # or it is someone else that wants to stop
            willLead = willLead or (pseudo != self.player.pseudo and stopScan < time.time())
            # or it is someone else that slept for too long (crash?)
            willLead = willLead or (pseudo != self.player.pseudo and nextScan < time.time())
            if  willLead: # We are the scanner => we should scan
                if pseudo is None:
                    log(None, "Shrib empty, we will take the scan lead")
                elif pseudo == self.player.pseudo:
                    log(None, "We are the alliance scanner for %s" % str(stopScan - time.time()))
                elif pseudo != self.player.pseudo and stopScan < time.time():
                    log(None, "Current scanner wants to stop, we will take the scan lead")
                elif pseudo != self.player.pseudo and nextScan < time.time():
                    log(None, "Current scanner didn't scan, we will take the scan lead")
                allianceRequest = Request(ia.alliancePage, {})
                ia.execRequest(allianceRequest)
                self.player.getFleetsFromStringFromAlliance(allianceRequest.content)
            else: # there was a scan (probably)
                log(None, "We are getting scans from %s" % pseudo)
                self.player.getFleetsFromStringFromAlliance(content)
        else:
            self.player.getFleets()
        log(None, "Scanned fleets")
        ennemyFleetInc = False
        discordMessageToSend = ""
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
                        discordMessageToSend += "\n" + message
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
                    if self.player.getTechLevel(106) < 8 or rapport.combatResult == 1 or (rapport.combatResult == 0 and not fleet.isDestroy()):
                        #if we (the defender) loose, or if it's a tie and it's not a moon destruction mission
                        log(None, "The incoming battle isn't in our favor, initiating evasion")
                        if targetPlanet.ships: #if there are some ships to send
                            try:
                                targetPlanet.sendFleet(ia.config.escapeTarget, Fleet.transportCode, targetPlanet.ships, [0, 0, 0], speed=1, allRessources=True)
                                targetPlanet.scanRessourcesUsingRequest(self.player.lastRequest)
                            except:
                                log(targetPlanet, "Error while sending the fleet for evasion")
                        else:
                            targetPlanet.scan()
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
        if ia.config.activateDefenderDiscordPing and ennemyFleetInc:
            try:
                ia.pingUser(discordMessageToSend)
            except:
                log(None, "Error while pinging Discord user. Make sure the webhook is correct.")
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
        if ia.config.activateAllianceScan:
            pseudo, stopScan, nextScan, content = ia.decodeShrib()
            willTakeLead = False
            # if there is currently no one scanning
            willTakeLead = willTakeLead or (pseudo is None)
            # or it is someone else that wants to stop
            willTakeLead = willTakeLead or (pseudo != self.player.pseudo and stopScan < time.time())
            # or it is someone else that slept for too long (crash?)
            willTakeLead = willTakeLead or (pseudo != self.player.pseudo and nextScan < time.time())
            if willTakeLead: # we begin to scan for 2 to 6 hours
                log(None, "We are taking the lead for scanning for the alliance")
                ia.storeShrib(ia.encodeShrib(self.player.pseudo, time.time() + 4*3600*(0.5+random.random()), newTask.t, self.player.lastRequest.content))
            elif (pseudo == self.player.pseudo) : # We are the scanner => we should publish
                # even if we wanted to stop, we publish with the expired stopScan time
                # that way if there are others that can scan, they will probably take the lead
                # and if for some reason they can't, then we are still scanning for them
                log(None, "Giving other members the scans")
                ia.storeShrib(ia.encodeShrib(self.player.pseudo, stopScan, newTask.t, self.player.lastRequest.content))
            else:
                # someone else is scanning, we wait for their scan
                newTask = ScanFleetsTask(nextScan + 30, self.player, randomAdditionnalWait=0)
        ia.addTask(newTask)
