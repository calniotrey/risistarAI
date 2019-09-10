import requests
import os
import heapq
import re
import sys
import threading
import time
from BuildOrder import BuildOrder
from CombatReport import CombatReport
from Config import Config
from Player import Player
from Request import Request
from tasks.Task import Task
from tasks.PickOfficerTask import PickOfficerTask
from tasks.PlanningTask import PlanningTask
from tasks.ScanFleetsTask import ScanFleetsTask
from UtilitiesFunctions import log

with open("secret.txt") as file:
    pseudo = file.readline().replace("\n", "")
    password = file.readline().replace("\n", "")  # en clair

class IA:
    config = Config.load()
    error = config.getError()
    if error is not None:
        print(error)
        sys.exit("Bad configuration !")

    domain              = config.domain
    mainURL             = "https://" + domain + "/index.php?"
    buildingPage        = "https://" + domain + "/game.php?page=buildings"
    overviewPage        = "https://" + domain + "/game.php?page=overview"
    renamingPage        = "https://" + domain + "/game.php?page=overview&mode=rename&name="
    sendBackFleetPage   = "https://" + domain + "/game.php?page=fleetTable&action=sendfleetback"
    sendFleetStep1Page  = "https://" + domain + "/game.php?page=fleetStep1"
    sendFleetStep2Page  = "https://" + domain + "/game.php?page=fleetStep2"
    sendFleetStep3Page  = "https://" + domain + "/game.php?page=fleetStep3"
    scanShipsPage       = "https://" + domain + "/game.php?page=fleetTable"
    buildDefPage        = "https://" + domain + "/game.php?page=shipyard&mode=defense"
    buildShipPage       = "https://" + domain + "/game.php?page=shipyard&mode=fleet"
    researchPage        = "https://" + domain + "/game.php?page=research"
    officerPage         = "https://" + domain + "/game.php?page=officier"
    battleSimulatorPage = "https://" + domain + "/game.php?page=battleSimulator&mode=send"
    battleRapportPage   = "https://" + domain + "/game.php?page=raport&raport="

    planetNameParser = re.compile(r'>(.*) \[(.*)\]')
    buildingNameParser = re.compile(r'\A([^\(]+)(?:\(.* (\d*))?')
    metalProductionParser = re.compile(r'production: ((?:\d|\.)+),\s+valueElem: "current_metal"')
    crystalProductionParser = re.compile(r'production: ((?:\d|\.)+),\s+valueElem: "current_crystal"')
    deutProductionParser = re.compile(r'production: ((?:\d|\.)+),\s+valueElem: "current_deuterium"')
    ressourcesParser = re.compile(r'(\d+) (\w+);')
    energyParser = re.compile(r'(-?\d+)./.(\d+)')

    def __init__(self, pseudo=None, password=None, lastCookie=None):
        self.session = requests.session()
        if self.config.userAgent is not None:
            self.session.headers.update({'User-Agent': self.config.userAgent})
        if lastCookie is not None:
            self.changeCookie(lastCookie)
        self.player = Player(pseudo, password, "Risistar", self)
        self.player.connexion()
        self.player.extractInfos(planets=True, darkMatter=True)
        self.tasks = {}
        self.tasks[Task.lowPrio   ] = [] #building, technos ...
        self.tasks[Task.middlePrio] = [] #scanning fleets
        self.tasks[Task.highPrio  ] = [] #evading ennemy fleet
        self.customBuildOrderDict = {}
        self._stop = False
        if self.config.activateAutoBuild:
            self.loadCustomBuildOrders()
            self.pairCustomBuildOrdersToPlanets()
            for p in self.player.planets:
                if not p.isMoon:
                    self.addTask(PlanningTask(time.time(), p))
        if self.config.activateAutoFleetScan:
            self.addTask(ScanFleetsTask(time.time(), self.player, 0))
        if self.config.activatePickingOfficers:
            self.addTask(PickOfficerTask(time.time(), self.player))

    def loadCustomBuildOrders(self):
        buildOrderDirectory = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.config.customBuildOrdersDirectoryName)
        if os.path.exists(buildOrderDirectory):
            buildOrderFiles = [f for f in os.listdir(buildOrderDirectory) if os.path.isfile(os.path.join(buildOrderDirectory, f))]
            for buildOrderFile in buildOrderFiles:
                buildOrderName = buildOrderFile.split(".")[0]
                buildOrderFilePath = os.path.join(buildOrderDirectory, buildOrderFile)
                buildOrder = BuildOrder(buildOrderName, filePath=buildOrderFilePath)
                self.customBuildOrderDict[buildOrderName] = buildOrder

    def pairCustomBuildOrdersToPlanets(self):
        with open(self.config.customBuildOrdersPairingFile) as file:
            l = file.readline()
            while l != "":
                l = l.replace("\n", "")
                if len(l) and l[0] != "#":
                    s = l.split("=")
                    cBOName = s[-1]
                    customBuildOrder = self.customBuildOrderDict.get(cBOName)
                    if customBuildOrder:
                        planetName = s[0]
                        for planetNameAddon in s[1:-1]:
                            planetName += "=" + planetNameAddon #allows spaces in the planet name
                        for planet in self.player.getOwnPlanetsByName(planetName):
                            planet.customBuildOrder = customBuildOrder
                l = file.readline()

    def addTask(self, t):
        heapq.heappush(self.tasks[t.prio], t)

    def run(self):
        stop = False
        while not stop:
            stop = True
            for prio in Task.descendingPrio:
                if len(self.tasks[prio]) and self.tasks[prio][0].t < time.time():
                    taskToExecute = heapq.heappop(self.tasks[prio])
                    taskToExecute.execute()
                    stop = False

    def permaRun(self, longestWait=10):
        while not self._stop:
            self.run()
            timeToSleep = self.timeToNextTask()
            if timeToSleep is not None and timeToSleep > 0:
                time.sleep(min(timeToSleep, longestWait))
        log(None, "Stopped")

    def timeToNextTask(self):
        nextTaskTime = None
        for prio in Task.descendingPrio:
            if len(self.tasks[prio]) and (nextTaskTime is None or self.tasks[prio][0].t < nextTaskTime):
                nextTaskTime = self.tasks[prio][0].t
        if nextTaskTime == None:
            log(None, "No more tasks ! ALERT")
            return None
        return nextTaskTime - time.time()

    def permaRunDetached(self):
        threading.Thread(target=self.permaRun).start()

    def stop(self):
        log(None, "Stopping")
        self._stop = True

    def execRequest(self, req):
        req.connect(self.session)
        if """var loginError = "Votre session a expir""" in req.content:
            #if we were disconnected we will try to reconnect once
            log(None, "Reconnecting")
            self.player.connexion()
            req.connect(self.session)
        self.player.lastRequest = req

    def changeCookie(self, newCookie):
        log(None, "Changing cookie : 2Moons = " + newCookie)
        self.session.cookies.set('2Moons', newCookie, domain=self.domain)

    def pingUser(self, message=""):
        data = {}
        data["content"] = "<@" + self.config.idToPing + "> " + message
        self.session.post(self.config.webhookUrl, data)

    def simulateCombat(self, fleet1, fleet2, bonus1=[0, 0, 0], bonus2=[0, 0, 0], ressources=[0, 0, 0]):
        payload = {}
        payload["battleinput[0][1][901]"] = ressources[0]
        payload["battleinput[0][1][902]"] = ressources[1]
        payload["battleinput[0][1][903]"] = ressources[2]
        payload["battleinput[0][0][109]"] = bonus1[0]
        payload["battleinput[0][0][110]"] = bonus1[1]
        payload["battleinput[0][0][111]"] = bonus1[2]
        payload["battleinput[0][1][109]"] = bonus2[0]
        payload["battleinput[0][1][110]"] = bonus2[1]
        payload["battleinput[0][1][111]"] = bonus2[2]
        for shipId in fleet1.keys():
            payload["battleinput[0][0][" + shipId + "]"] = fleet1[shipId]
        for shipId in fleet2.keys():
            payload["battleinput[0][1][" + shipId + "]"] = fleet2[shipId]
        simulatorReq = Request(self.battleSimulatorPage, payload)
        self.execRequest(simulatorReq)
        rapportReq = Request(self.battleRapportPage + simulatorReq.content.replace('"', ''), payload)
        self.execRequest(rapportReq)
        return CombatReport.analyzeCombatReport(rapportReq.content)
