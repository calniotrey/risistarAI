import math
import time
from bs4 import BeautifulSoup
from Building import Building
from Codes import Codes
from Request import Request
from tasks.BuildingTask import BuildingTask
from UtilitiesFunctions import log

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
        self.isMoon = "(Lune)" in name
        self.sizeUsed = None
        self.sizeMax = None
        self.ships = {}
        self.customBuildOrder = None

    def buildingById(self, id):
        for b in self.batiments:
            if b.id == id:
                return b
        return None

    def buildingLevelById(self, id): #returns the level or 0 if the building isn't build yet
        for b in self.batiments:
            if b.id == id:
                return b.level
        return 0

    def buildingByType(self, type):
        for b in self.batiments:
            if b.type == type:
                return b
        return None

    def getNameWithSize(self):
        return self.name + " (" + str(self.sizeUsed) + "/" + str(self.sizeMax) + ")"

    def getSize(self):
        reqP = Request(self.player.ia.overviewPage + "&cp=" + self.id, {})
        self.player.ia.execRequest(reqP)
        soup = BeautifulSoup(reqP.content, "html.parser")
        #parse the size
        self.sizeUsed = int(soup.find(attrs={"title": 'Cases occupées'}).text)
        self.sizeMax = int(soup.find(attrs={"title": 'Cases max. disponibles'}).text)

    def rename(self, name): #Returns true if renaming worked
        reqP = Request(self.player.ia.renamingPage + name + "&cp=" + self.id, {})
        response = self.player.ia.execRequest(reqP)
        if reqP.response.status_code == 200:
            self.name = name
            return True
        return False

    def planBuilding(self):
        config = self.player.ia.config #to make lines smaller
        buildingId = None
        if config.activateCustomBuildOrders and self.customBuildOrder is not None:
            buildingId = self.customBuildOrder.nextBuilding(self) #id of the building to build
            if buildingId is None:
                if self.customBuildOrder.useDefaultBuildPlanWhenEmpty:
                    buildingId = self.defaultPlanBuildingWithoutHangars()
                else:
                    log(self, "No more building planned by the custom build order !")
                    return None
        else:
            buildingId = self.defaultPlanBuildingWithoutHangars()
        buildingId = self.planHangarsInstead(buildingId)
        building = self.buildingById(buildingId)
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

    def defaultPlanBuildingWithoutHangars(self):
        config = self.player.ia.config #to make lines smaller
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
        buildingId = Codes.strToId[b]
        return buildingId

    def planHangarsInstead(self, b):
        building = self.buildingById(b)
        while not building.upgradable([self.metalStorage, self.crystalStorage, self.deutStorage]):
            # on ne peut pas stocker assez de ressources pour le construire
            b = 'Hangar de Métal'
            if building.upgradeCost[1] > self.crystalStorage:
                b = 'Hangar de Cristal'
            elif building.upgradeCost[2] > self.deutStorage:
                b = 'Réservoir de Deutérium'
            building = self.buildingByType(b)
        buildingId = building.id
        return buildingId

    def upgradableBuildings(self, ressources):
        return [bat for bat in self.batimens if bat.upgradable(ressources)]

    def scan(self):
        reqB = Request(self.player.ia.buildingPage + "&cp=" + self.id, {})
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
                nameAndLevel = self.player.ia.buildingNameParser.findall(nameAndLevelText)
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
                for r in self.player.ia.ressourcesParser.findall(costText):
                    if r[1] == "Metal":
                        res[0] = int(r[0])
                    if r[1] == "Crystal":
                        res[1] = int(r[0])
                    if r[1] == "Deut":
                        res[2] = int(r[0])
                form = divs[4].find("input", attrs={"name": "building"})
                id = Codes.strToId.get(name)
                b = Building(name, id, self, level)
                b.upgradeCost = res
                b.upgradeTime = upgradeTime
                self.batiments.append(b)

        self.metal = float(soup.find(id="current_metal").attrs['data-real'])
        self.crystal = float(soup.find(id="current_crystal").attrs['data-real'])
        deutTd = soup.find(id="current_deuterium")
        energyText = deutTd.nextSibling.span.text.replace(".", "") #-40 / 0 for example
        e = self.player.ia.energyParser.findall(energyText)
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
            self.metalProduction = float(self.player.ia.metalProductionParser.findall(script)[0]) / 3600
            self.crystalProduction = float(self.player.ia.crystalProductionParser.findall(script)[0]) / 3600
            self.deutProduction = float(self.player.ia.deutProductionParser.findall(script)[0]) / 3600
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

    def scanShips(self):
        scanShipsRequest = Request(self.player.ia.scanShipsPage + "&cp=" + self.id, {})
        self.player.ia.execRequest(scanShipsRequest)
        soup = BeautifulSoup(scanShipsRequest.content, "html.parser")
        #parse all available ships
        shipsTr = soup.find("table", class_="table519").find_all("tr")[2:-2] #the first and last 2 are headers
        ships = {}
        for shipTr in shipsTr:
            shipTd = shipTr.find_all("td")[1]
            shipId = int(shipTd.attrs["id"].split("_")[0].replace("ship", ""))
            shipAmount = int(shipTd.text.replace(".", ""))
            ships[shipId] = shipAmount
        self.ships = ships

    def sendFleet(self, target, missionType, ships, ressources, speed=10, staytime=1, allRessources=False):
        firstPayload = {}
        for shipId in ships.keys():
            if shipId not in [212, 227, 228, 229, 230, 231]:
                firstPayload["ship" + str(shipId)] = ships[shipId]
        sendFleetStep1 = Request(self.player.ia.sendFleetStep1Page + "&cp=" + self.id, firstPayload)
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
            sendFleetStep2 = Request(self.player.ia.sendFleetStep2Page + "&cp=" + self.id, secondPayload)
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
            sendFleetStep3 = Request(self.player.ia.sendFleetStep3Page + "&cp=" + self.id, thirdPayload)
            self.player.ia.execRequest(sendFleetStep3)
            log(self, "Fleet sent")
        else:
            log(self, "Error while sending the fleet", isError=True)

    def buildDefenses(self, defenses):
        payload = {}
        for id in defenses.keys():
            payload["fmenge[" + str(id) + "]"] = defenses[id]
        buildDefReq = Request(self.player.ia.buildDefPage + "&cp=" + self.id, payload)
        self.player.ia.execRequest(buildDefReq)

    def buildShips(self, ships):
        payload = {}
        for id in ships.keys():
            payload["fmenge[" + str(id) + "]"] = ships[id]
        buildShipReq = Request(self.player.ia.buildShipPage + "&cp=" + self.id, payload)
        self.player.ia.execRequest(buildShipReq)

    def getPosAsString(self):
        return str(self.pos[0]) + ":" + str(self.pos[1]) + ":" + str(self.pos[2]) + ":" + str(self.pos[3])
