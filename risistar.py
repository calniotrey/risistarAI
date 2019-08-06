import requests
import sys, time, re
import heapq
import threading
import random
import math
from bs4 import BeautifulSoup
from Config import Config

file = open("secret.txt")
pseudo = file.readline().replace("\n", "")
password = file.readline().replace("\n", "")  # en clair
file.close()

config = Config.load()
error = config.getError()
if error is not None:
    print(error)
    sys.exit("Bad configuration !")

domain             = config.domain
mainURL            = "https://" + domain + "/index.php?"
buildingPage       = "https://" + domain + "/game.php?page=buildings"
overviewPage       = "https://" + domain + "/game.php?page=overview"
renamingPage       = "https://" + domain + "/game.php?page=overview&mode=rename&name="
sendBackFleetPage  = "https://" + domain + "/game.php?page=fleetTable&action=sendfleetback"
sendFleetStep1Page = "https://" + domain + "/game.php?page=fleetStep1"
sendFleetStep2Page = "https://" + domain + "/game.php?page=fleetStep2"
sendFleetStep3Page = "https://" + domain + "/game.php?page=fleetStep3"
getShipsPage       = "https://" + domain + "/game.php?page=fleetTable"
buildDefPage       = "https://" + domain + "/game.php?page=shipyard&mode=defense"
buildShipPage      = "https://" + domain + "/game.php?page=shipyard&mode=fleet"

session = requests.session()
session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:67.0) Gecko/20100101 Firefox/67.0'})

planetNameParser = re.compile(r'>(.*) \[(.*)\]')
buildingNameParser = re.compile(r'\A([^\(]+)(?:\(.* (\d*))?')
metalProductionParser = re.compile(r'production: ((?:\d|\.)+),\s+valueElem: "current_metal"')
crystalProductionParser = re.compile(r'production: ((?:\d|\.)+),\s+valueElem: "current_crystal"')
deutProductionParser = re.compile(r'production: ((?:\d|\.)+),\s+valueElem: "current_deuterium"')
ressourcesParser = re.compile(r'(\d+) (\w+);')
energyParser = re.compile(r'(-?\d+)./.(\d+)')

def log(planet, str):
    if planet != None:
        print(time.strftime("%H:%M:%S"), " [", planet.id, "] ", str, sep='')
    else:
        print(time.strftime("%H:%M:%S"), " [   ] ", str, sep='')

def setupRisistarCookie(cookieValue):
    session.cookies.set('2Moons', cookieValue, domain=domain)

def pingUser(message=""):
    data = {}
    data["content"] = "<@" + config.idToPing + "> " + message
    session.post(config.webhookUrl, data)

class Request:
    def __init__(self, url, payload):
        self.url = url
        self.payload = payload
        self.response = None
        self.date = time.time()
        self.content = None

    def connect(self):
        self.response = session.post(self.url, data=self.payload)
        self.date = time.time()
        self.content = self.response.content.decode().replace("\n", "").replace("\t", "")
        return self.response

    def saveToFile(self, filePath):
        if (self.response != None):
            with open(filePath, 'wb') as file:
                file.write(self.response.content)

class Task:
    def __init__(self, t):
        self.t = t
        self.prio = IA.lowPrio

    def __gt__(self, other):
        return self.t > other.t

    def __ge__(self, other):
        return self.t >= other.t

class IA:
    highPrio   = 0
    middlePrio = 1
    lowPrio    = 2
    descendingPrio = [highPrio, middlePrio, lowPrio]

    def __init__(self, pseudo, password):
        self.player = Player(pseudo, password, "Risistar", self)
        self.player.connexion()
        self.player.extractInfos(planets=True)
        self.tasks = {}
        self.tasks[IA.lowPrio   ] = [] #building, technos ...
        self.tasks[IA.middlePrio] = [] #scanning fleets
        self.tasks[IA.highPrio  ] = [] #evading ennemy fleet
        self._stop = False
        if config.activateAutoBuild:
            for p in self.player.planets:
                if not p.isMoon:
                    self.addTask(PlanningTask(time.time(), p))
        if config.activateAutoFleetScan:
            self.addTask(ScanFleetsTask(time.time(), self.player, 0))

    def addTask(self, t):
        heapq.heappush(self.tasks[t.prio], t)

    def run(self):
        stop = False
        while not stop:
            stop = True
            for prio in IA.descendingPrio:
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
        for prio in IA.descendingPrio:
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
        req.connect()
        if """var loginError = "Votre session a expir""" in req.content:
            #if we were disconnected we will try to reconnect once
            log(None, "Reconnecting")
            self.player.connexion()
            req.connect()
        self.player.lastRequest = req

    def changeCookie(self, newCookie):
        log(None, "Changing cookie : 2Moons = " + newCookie)
        session.cookies.set('2Moons', newCookie, domain=domain)

class ScanFleetsTask(Task):
    def __init__(self, t, player, randomAdditionnalWait=config.randomAdditionnalTimeBetweenScans):
        self.t = t + random.random() * randomAdditionnalWait
        self.player = player
        self.prio = IA.middlePrio

    def execute(self):
        self.player.getFleets()
        log(None, "Scanned fleets")
        ennemyFleetInc = False
        for fleet in self.player.fleets.values():
            targetPlanet = self.player.getOwnPlanetByPosition(fleet.target)
            if fleet.type == "attack" and targetPlanet is not None and fleet.isGoing: #if we are getting attacked
                log(None, "HOSTILE FLEET targeting " + targetPlanet.name + " in " + str(fleet.eta - time.time()))
                ennemyFleetInc = True
                try:
                    if config.activateDefenderDiscordPing:
                        message = config.customAttackNotificationMessage
                        message = message.replace("{targetPlanet.name}", targetPlanet.name)
                        message = message.replace("{targetPlanet.position}", targetPlanet.getPosAsString())
                        message = message.replace("{fleet.ttd}", str(int(fleet.eta - time.time())))
                        pingUser(message)
                    minimumTimeWindowToLaunch = 2 * config.minimumTimeBetweenScans + config.randomAdditionnalTimeBetweenScans
                    shouldEvade = (fleet.eta - time.time()) < minimumTimeWindowToLaunch
                    shouldEvade = shouldEvade and config.activateAutoEvasion
                    shouldEvade = shouldEvade and (time.time() - fleet.firstSpotted) >= config.minimumSpottingTime
                    if shouldEvade:
                        targetPlanet.getShips()
                        targetPlanet.sendFleet(config.escapeTarget, Fleet.transportCode, targetPlanet.ships, [0, 0, 0], speed=1, allRessources=True)
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
                except:
                    print("ERROR LOL")
        try:
            if not ennemyFleetInc:
                for fleet in self.player.fleets.values():
                    if fleet.target == config.escapeTarget:
                        fleet.sendBack()
        except:
            print("Erreur lors de l'annulation")
        newTask = ScanFleetsTask(time.time() + config.minimumTimeBetweenScans, self.player)
        self.player.ia.addTask(newTask)

class BuildingTask(Task):
    def __init__(self, t, bat):
        self.t = t
        self.bat = bat
        self.prio = IA.lowPrio

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

class PlanningTask(Task):
    def __init__(self, t, planet):
        self.t = t
        self.planet = planet
        self.prio = IA.lowPrio

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
            if self.planet.sizeUsed < self.planet.sizeMax:
                log(self.planet, "Planning building")
                newTask = self.planet.planBuilding()
                log(self.planet, "Done planning building")
                log(self.planet, "Planning to build a " + newTask.bat.type + " to level " + str(newTask.bat.level + 1) + " in " + str(newTask.t - time.time()))
            else:
                log(self.planet, "Planet filled ! Retrying in 10 minutes")
                newTask = PlanningTask(time.time() + 600, self.planet)
                self.planet.player.ia.addTask(newTask)


class Building:
    buildingCode = {}
    buildingCode["Mine de Métal"              ] = 1
    buildingCode["Mine de Cristal"            ] = 2
    buildingCode["Synthétiseur de Deutérium"  ] = 3
    buildingCode["Centrale éléctrique Solaire"] = 4
    buildingCode["Centrale de fusion"         ] = 12
    buildingCode["Usine de Robots"            ] = 14
    buildingCode["Chantier Spatial"           ] = 21
    buildingCode["Hangar de Métal"            ] = 22
    buildingCode["Hangar de Cristal"          ] = 23
    buildingCode["Réservoir de Deutérium"     ] = 24
    buildingCode["Laboratoire de Recherche"   ] = 31
    buildingCode["Dépôt d'Alliance"           ] = 34
    buildingCode["Silo de Missiles"           ] = 44

    def __init__(self, type, id, planet, level=0):
        self.type = type
        self.level = level
        self.planet = planet
        self.id = id
        if id is None: #if the building isn't upgradable
            self.id = Building.buildingCode.get(type, None)
        self.upgradeTime = None
        self.upgradeCost = None

    def upgradable(self, ressources):
        for i in range(0,3):
            if self.upgradeCost[i] > ressources[i]:
                return False
        return True

    def upgrade(self):
        if self.id != None:
            payload = {'cmd': 'insert', 'building': self.id}
            reqB = Request(buildingPage + "&cp=" + self.planet.id, payload)
            self.planet.player.ia.execRequest(reqB)
            return reqB

class Planet:
    def __init__(self, id, name, position, player):
        self.id = id        #string
        self.name = name
        self.pos = position
        self.player = player
        self.batiments = []
        self.construction = []
        self.metal = None
        self.metalStorage = None
        self.metalProduction = None
        self.crystal = None
        self.crystalStorage = None
        self.crystalProduction = None
        self.deut = None
        self.deutStorage = None
        self.deutProduction = None
        self.energy = None
        self.energyStorage = None
        self.lastExtracedInfosDate = None
        self.upgradingEnd = 0 #when the last upgrade will finish. Either 0 or time.time() + rest
        self.isMoon = "Lune" in name
        self.sizeUsed = None
        self.sizeMax = None
        self.ships = {}

    def buildingById(self, id):
        for b in self.batiments:
            if b.id == id:
                return b
        return None

    def buildingByType(self, type):
        for b in self.batiments:
            if b.type == type:
                return b
        return None

    def getNameWithSize(self):
        return self.name + " (" + str(self.sizeUsed) + "/" + str(self.sizeMax) + ")"

    def getSize(self):
        reqP = Request(overviewPage + "&cp=" + self.id, {})
        self.player.ia.execRequest(reqP)
        soup = BeautifulSoup(reqP.content, "html.parser")
        #parse the size
        self.sizeUsed = int(soup.find(attrs={"title": 'Cases occupées'}).text)
        self.sizeMax = int(soup.find(attrs={"title": 'Cases max. disponibles'}).text)

    def rename(self, name): #Returns true if renaming worked
        reqP = Request(renamingPage + name + "&cp=" + self.id, {})
        response = self.player.ia.execRequest(reqP)
        if reqP.response.status_code == 200:
            self.name = name
            return True
        return False

    def planBuilding(self):
        b = None
        if self.energy < 0:
            b = 'Centrale éléctrique Solaire'
        else:
            metalMine = self.buildingByType('Mine de Métal').level
            crystalMine = self.buildingByType('Mine de Cristal').level
            deutMine = self.buildingByType('Synthétiseur de Deutérium').level
            robotFactory = self.buildingByType('Usine de Robots').level
            if metalMine >= config.robotStartingLevel and (metalMine / config.robotRatio > robotFactory) and self.buildingByType('Usine de Robots').upgradeCost[2] <= self.deut:
                b = 'Usine de Robots'
            elif crystalMine > deutMine + 5:
                b = 'Synthétiseur de Deutérium'
            else:
                if metalMine > crystalMine + 2:
                    b = 'Mine de Cristal'
                else:
                    b = 'Mine de Métal'
        building = self.buildingByType(b)
        while not building.upgradable([self.metalStorage, self.crystalStorage, self.deutStorage]):
            # on ne peut pas stocker assez de ressources pour le construire
            b = 'Hangar de Métal'
            if building.upgradeCost[1] > self.crystalStorage:
                b = 'Hangar de Cristal'
            elif building.upgradeCost[2] > self.deutStorage:
                b = 'Réservoir de Deutérium'
            building = self.buildingByType(b)
        #now we need to know how much to wait
        t = [x for x in building.upgradeCost] #the ressources needed
        t[0] = (t[0] - self.metal) / self.metalProduction
        t[1] = (t[1] - self.crystal) /  self.crystalProduction
        if self.deutProduction == 0:
            t[2] = 0 if (self.deut - t[2]) >= 0 else math.inf
        else:
            t[2] = (t[2] - self.deut) /  self.deutProduction
        t.append(0) #to ensure that the task execute time is at least time.time()
        timeToWait = max(t)
        task = BuildingTask(time.time() + timeToWait, building)
        self.player.ia.addTask(task)
        return task

    def upgradableBuildings(self, ressources):
        return [bat for bat in self.batimens if bat.upgradable(ressources)]

    def scan(self):
        reqB = Request(buildingPage + "&cp=" + self.id, {})
        self.player.ia.execRequest(reqB)
        self.scanUsingRequest(reqB)

    def scanUsingRequest(self, reqB):
        soup = BeautifulSoup(reqB.content, "html.parser")
        #parse all available buildings
        bats = soup.find(id="content").find_all("div", recursive=False)
        self.batiments = []
        self.upgradingEnd = 0
        for b in bats:
            if b.attrs.get("id") == "buildlist": #if it's a building currently building
                self.upgradingEnd = float(b.find(class_="timer").attrs["data-time"]) #at the end of the loop, it will be the end of the last building
            else:
                nameAndLevelText = b.find("a").text
                nameAndLevel = buildingNameParser.findall(nameAndLevelText)
                name = nameAndLevel[0][0]
                level = 0
                if nameAndLevel[0][1] != '':
                    level = int(nameAndLevel[0][1])
                divs = b.find_all("div", recursive=False)
                upgradeTimeString = divs[1].span.text
                upgradeTimeTab = upgradeTimeString.split("d ")
                if len(upgradeTimeTab) == 1:
                    upgradeTimeTab = ['0', upgradeTimeTab[0]]
                upgradeTimeDay = int(upgradeTimeTab[0])
                upgradeTimeTab = upgradeTimeTab[1].split("h ")
                upgradeTimeHour = int(upgradeTimeTab[0])
                upgradeTimeTab = upgradeTimeTab[1].split("m ")
                upgradeTimeMin = int(upgradeTimeTab[0])
                upgradeTimeTab = upgradeTimeTab[1].split("s")
                upgradeTimeSec = int(upgradeTimeTab[0])
                upgradeTime = (((upgradeTimeDay * 24) + upgradeTimeHour) * 60 + upgradeTimeMin) * 60 + upgradeTimeSec
                m = divs[2].span.find(alt="Métal")
                if m != None:
                    m.replace_with("Metal;")
                c = divs[2].span.find(alt="Crystal")
                if c != None:
                    c.replace_with("Crystal;")
                d = divs[2].span.find(alt="Deutérium")
                if d != None:
                    d.replace_with("Deut;")
                costText = divs[2].span.text.replace(".", "")
                res = [0, 0, 0]
                for r in ressourcesParser.findall(costText):
                    if r[1] == "Metal":
                        res[0] = int(r[0])
                    if r[1] == "Crystal":
                        res[1] = int(r[0])
                    if r[1] == "Deut":
                        res[2] = int(r[0])
                form = divs[4].find("input", attrs={"name": "building"})
                id = None
                if form != None:
                    id = form.attrs['value']
                b = Building(name, id, self, level)
                b.upgradeCost = res
                b.upgradeTime = upgradeTime
                self.batiments.append(b)

        self.metal = float(soup.find(id="current_metal").attrs['data-real'])
        self.crystal = float(soup.find(id="current_crystal").attrs['data-real'])
        deutTd = soup.find(id="current_deuterium")
        energyText = deutTd.nextSibling.span.text.replace(".", "") #-40 / 0 for example
        e = energyParser.findall(energyText)
        self.energy = int(e[0][0])
        self.energyStorage = int(e[0][1])
        self.deut = float(deutTd.attrs['data-real'])
        self.metalStorage = float(soup.find(id="max_metal").text.replace(".", ""))
        self.crystalStorage = float(soup.find(id="max_crystal").text.replace(".", ""))
        self.deutStorage = float(soup.find(id="max_deuterium").text.replace(".", ""))
        script = soup.find_all("script", attrs={"type":"text/javascript"})[-1].text
        if self.isMoon: #Moons don't produce
            self.metalProduction = 0
            self.crystalProduction = 0
            self.deutProduction = 0
        else:
            self.metalProduction = float(metalProductionParser.findall(script)[0]) / 3600
            self.crystalProduction = float(crystalProductionParser.findall(script)[0]) / 3600
            self.deutProduction = float(deutProductionParser.findall(script)[0]) / 3600
        sizeUsed = 0
        for batiment in self.batiments:
            sizeUsed += batiment.level
        self.sizeUsed = sizeUsed

    def scanRessourcesUsingRequest(self, req):
        soup = BeautifulSoup(req.content, "html.parser")
        self.metal = float(soup.find(id="current_metal").attrs['data-real'])
        self.crystal = float(soup.find(id="current_crystal").attrs['data-real'])
        self.deut = float(soup.find(id="current_deuterium").attrs['data-real'])

    def expectedRessources(self, timeTarget=time.time(), takeStorageInAccount=True):
        t = (timeTarget - self.lastExtracedInfosDate) / 3600
        em = self.metal + self.metalProduction * t
        ec = self.crystal + self.crystalProduction * t
        ed = self.deut + self.deutProduction * t
        if (takeStorageInAccount):
            return [min(em, self.metalStorage), min(ec, self.crystalStorage), min(ed, self.deutStorage)]
        return [em, ec, ed]

    def getShips(self):
        getShipsRequest = Request(getShipsPage + "&cp=" + self.id, {})
        self.player.ia.execRequest(getShipsRequest)
        soup = BeautifulSoup(getShipsRequest.content, "html.parser")
        #parse all available ships
        shipsTr = soup.find("table", class_="table519").find_all("tr")[2:-2] #the first and last 2 are headers
        ships = {}
        for shipTr in shipsTr:
            shipTd = shipTr.find_all("td")[1]
            shipId = shipTd.attrs["id"].split("_")[0]
            shipAmount = int(shipTd.text)
            ships[shipId] = shipAmount
        self.ships = ships

    def sendFleet(self, target, missionType, ships, ressources, speed=10, staytime=1, allRessources=False):
        firstPayload = {}
        for ship in ships.keys():
            firstPayload[ship] = ships[ship]
        sendFleetStep1 = Request(sendFleetStep1Page + "&cp=" + self.id, firstPayload)
        self.player.ia.execRequest(sendFleetStep1)
        soup = BeautifulSoup(sendFleetStep1.content, "html.parser")
        tokenInput = soup.find("input", attrs={"name":"token"})
        if tokenInput is not None:
            token = tokenInput.attrs["value"]
            secondPayload = {}
            secondPayload["galaxy"] = target[0]
            secondPayload["system"] = target[1]
            secondPayload["planet"] = target[2]
            secondPayload["type"  ] = target[3] #1 = planet, 2 = CDR, 3 = moon
            secondPayload["speed" ] = speed #the speed in multiples of 10%
            secondPayload["token" ] = token
            sendFleetStep2 = Request(sendFleetStep2Page + "&cp=" + self.id, secondPayload)
            self.player.ia.execRequest(sendFleetStep2)
            thirdPayload = {}
            if allRessources:
                self.scanRessourcesUsingRequest(sendFleetStep2)
                ressources[0] = self.metal
                ressources[1] = self.crystal
                ressources[2] = self.deut
            soup = BeautifulSoup(sendFleetStep2.content, "html.parser")
            scriptRessources = soup.findAll("script")[-1].text
            fleetroom = int(scriptRessources.split(':"')[1].split('"')[0])
            consumption = int(scriptRessources.split(':"')[2].split('"')[0])
            fleetroom -= consumption
            thirdPayload["deuterium"] = min(ressources[2], fleetroom)
            fleetroom -= thirdPayload["deuterium"]
            thirdPayload["crystal"] = min(ressources[1], fleetroom)
            fleetroom -= thirdPayload["crystal"]
            thirdPayload["metal"] = min(ressources[0], fleetroom)
            fleetroom -= thirdPayload["metal"]
            thirdPayload["mission"  ] = missionType
            thirdPayload["staytime" ] = staytime
            thirdPayload["token"    ]  = token
            sendFleetStep3 = Request(sendFleetStep3Page + "&cp=" + self.id, thirdPayload)
            self.player.ia.execRequest(sendFleetStep3)
            log(self, "Fleet sent")
        else:
            log(self, "Error while sending the fleet")

    def buildDefenses(self, defenses):
        payload = {}
        for id in defenses.keys():
            payload["fmenge[" + str(id) + "]"] = defenses[id]
        buildDefReq = Request(buildDefPage + "&cp=" + self.id, payload)
        self.player.ia.execRequest(buildDefReq)

    def buildShips(self, ships):
        payload = {}
        for id in ships.keys():
            payload["fmenge[" + str(id) + "]"] = ships[id]
        buildShipReq = Request(buildShipPage + "&cp=" + self.id, payload)
        self.player.ia.execRequest(buildShipReq)

    def getPosAsString(self):
        return str(self.pos[0]) + ":" + str(self.pos[1]) + ":" + str(self.pos[2]) + ":" + str(self.pos[3])


class Fleet:
    attackCode     = 1
    transportCode  = 3
    deployCode     = 4
    stationCode    = 5
    spyCode        = 6
    colonizeCode   = 7
    expeditionCode = 15

    def __init__(self, player, id, origin, target, eta, type, isGoing):
        self.player = player
        self.id = id
        self.origin = origin
        self.target = target
        self.eta = eta
        self.isGoing = isGoing #either is going to target, or is coming back
        self.type = type
        self.isHostile = False
        self.firstSpotted = time.time()

    def isAttack(self):
        return self.type == "attack"

    def isSpy(self):
        return self.type == "espionage" or self.type == "ownespionage"

    def isHostileSpy(self):
        return self.type == "espionage"

    def isOwnSpy(self):
        return self.type == "ownespionage"

    def sendBack(self): #no check wether the fleet is ours
        sendBackRequest = Request(sendBackFleetPage, {"fleetID": self.id})
        self.player.ia.execRequest(sendBackRequest)

class Player:
    def __init__(self, pseudo, mdp, universe, ia):
        self.pseudo = pseudo
        self.mdp = mdp
        self.universe = universe
        self.darkMatter = None
        self.lastRequest = None
        self.lastExtracedInfosDate = None
        self.planets = []
        self.fleets = {} #friendly, own and hostile. Dictionnary id=>fleet
        self.ia = ia

    def connexion(self):
        payload = {
            'username' : self.pseudo,
            'password' : self.mdp,
            'universe' : self.universe,
        }
        connexionRequest = Request(mainURL + 'page=login', payload)
        connexionRequest.connect()
        self.lastRequest = connexionRequest
        if """var loginError = "Combinaison login""" in connexionRequest.content:
            log(None, "Login/Password incorrect")
            sys.exit("Login/Password incorrect")
        elif """var loginError = "Votre session a expir""" in connexionRequest.content:
            #if the cookie we setup was false
            log(None, "Bad Cookie. Clearing session cookies and trying to reconnect using credentials")
            session.cookies.clear()
            self.connexion()
        else:
            log(None, "Connected")
            log(None, "Cookie : @2Moons = " + session.cookies["2Moons"])

    def extractInfos(self, request=None, darkMatter=False, planets=True):
        if request == None:
            request = self.lastRequest
        if (request.response != None):
            content = request.content
            soup = BeautifulSoup(content, "html.parser")
            if darkMatter:
                self.darkMatter = float(soup.find(id="current_darkmatter").attrs['data-real'])
                self.lastExtracedInfosDate = time.time()
            if planets:
                ps = soup.find(id="planetSelector").find_all("option")
                self.planets = []
                for p in ps:
                    planet = planetNameParser.findall(str(p))
                    id = p.attrs['value']
                    name = planet[0][0]
                    position = [int(x) for x in planet[0][1].split(":")]
                    if "Lune" in name:
                        position.append(3)
                    else:
                        position.append(1)
                    pl = Planet(id, name, position, self)
                    self.planets.append(pl)
                    pl.scan()

    def getFleets(self):
        fleets = {}
        overviewRequest = Request(overviewPage, {})
        self.ia.execRequest(overviewRequest)
        soup = BeautifulSoup(overviewRequest.response.content, "html.parser")
        #parse all available buildings
        fleetsTd = soup.find_all("td", class_="fleets")
        for fleetTd in fleetsTd[::-1]: #invert the list so the smallest eta overrides the latest
            etaStr = fleetTd.attrs["data-fleet-end-time"]
            eta = float(etaStr)
            id = fleetTd.attrs["id"].split(etaStr)[1] #The etaStr is appended at the end of the id
            fleetSpan = fleetTd.parent.find("span")
            typeList = fleetSpan.attrs["class"]
            isGoing = (typeList[0] == "flight")
            type = typeList[1]
            aList = fleetSpan.findAll("a", class_=type)
            aList = [a for a in aList if not "tooltip" in a.attrs["class"]]
            originA = aList[0]
            targetA = aList[1]
            origin = [int(x) for x in originA.text[1:-1].split(":")]
            if "Lune" in originA.previous:
                origin.append(3)
            elif "CDR" in originA.previous:
                origin.append(2)
            else:
                origin.append(1)
            target = [int(x) for x in targetA.text[1:-1].split(":")]
            if "Lune" in targetA.previous:
                target.append(3)
            elif "CDR" in targetA.previous:
                target.append(2)
            else:
                target.append(1)
            fleet = Fleet(self, id, origin, target, eta, type, isGoing)
            ancientFleet = self.fleets.get(fleet.id)
            if ancientFleet is not None:
                fleet.firstSpotted = ancientFleet.firstSpotted
            fleets[fleet.id] = fleet
        self.fleets = fleets

    def getOwnPlanetByPosition(self, position):
        for p in self.planets:
            if p.pos == position:
                return p
        return None
