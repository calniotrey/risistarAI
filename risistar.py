import requests
import sys, time, re
import heapq
import threading
from bs4 import BeautifulSoup

file = open("secret.txt")
pseudo = file.readline().replace("\n", "")
password = file.readline().replace("\n", "")  # en clair
file.close()

domain       = "beta.risistar.fr"
mainURL      = "http://" + domain + "/index.php?"
buildingPage = "http://" + domain + "/game.php?page=buildings"
overviewPage = "http://" + domain + "/game.php?page=overview"
renamingPage = "http://" + domain + "/game.php?page=overview&mode=rename&name="
session = requests.session()

planetNameParser = re.compile(r'''>(.*) \[(.*)\]''')
buildingNameParser = re.compile(r'''\A([^\(]+)(?:\(.* (\d*))?''')
metalProductionParser = re.compile(r'''production: ((?:\d|\.)+),\s+valueElem: "current_metal"''')
crystalProductionParser = re.compile(r'''production: ((?:\d|\.)+),\s+valueElem: "current_crystal"''')
deutProductionParser = re.compile(r'''production: ((?:\d|\.)+),\s+valueElem: "current_deuterium"''')
ressourcesParser = re.compile(r'''(\d+) (\w+);''')
energyParser = re.compile(r'''(-?\d+)./.(\d+)''')

def log(planet, str):
    if planet != None:
        print(time.strftime("%H:%M:%S"), " [", planet.id, "] ", str, sep='')
    else:
        print(time.strftime("%H:%M:%S"), " [   ] ", str, sep='')

def setupRisistarCookie(cookieValue):
    session.cookies.set('2Moons', cookieValue, domain=domain)

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
    
    def __gt__(self, other):
        return self.t > other.t
            
    def __ge__(self, other):
        return self.t >= other.t

class IA:
    def __init__(self, pseudo, password):
        self.player = Player(pseudo, password, "Risistar", self)
        self.player.connexion()
        self.player.extractInfos(planets=True)
        self.h = []   #liste triée croissante selon le temps planifié
        self._stop = False
        for p in self.player.planets:
            if not p.isMoon:
                self.addTask(PlanningTask(time.time(), p))
    
    def addTask(self, t):
        heapq.heappush(self.h, t)
    
    def run(self):
        while len(self.h) and self.h[0].t < time.time():
            taskToExecute = heapq.heappop(self.h)
            taskToExecute.execute()

    def permaRun(self, longestWait=10):
        while not self._stop:
            self.run()
            timeToSleep = self.h[0].t - time.time()
            if timeToSleep > 0:
                time.sleep(min(timeToSleep, longestWait))
        log(None, "Stopped")
    
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

class BuildingTask(Task):
    def __init__(self, t, bat):
        self.t = t
        self.bat = bat
    
    def execute(self):
        req = self.bat.upgrade()
        self.bat.planet.scanUsingRequest(req)
        if self.bat.planet.upgradingEnd == 0: #the building wasn't upgraded
            log(self.bat.planet, "Waiting an additionnal second (SHOULDN'T HAPPEN NORMALLY)")
            newTask = BuildingTask(time.time() + 1, self.bat)
            self.bat.planet.player.ia.addTask(newTask)
        else:
            log(self.bat.planet, "Building " + self.bat.type + " to level " + str(self.bat.level + 1) + " in " + str(self.bat.upgradeTime))
            self.bat.planet.player.ia.addTask(PlanningTask(time.time() + self.bat.upgradeTime, self.bat.planet))

class PlanningTask(Task):
    def __init__(self, t, planet):
        self.t = t
        self.planet = planet
    
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
                log(self.planet, "Planet filled !")
                

class Building:
    buildingCode = {}
    buildingCode["Mine de Métal"              ] = 1
    buildingCode["Mine de Cristal"            ] = 2
    buildingCode["Synthétiseur de Deutérium"  ] = 3
    buildingCode["Centrale éléctrique Solaire"] = 4
    buildingCode["Usine de Robots"            ] = 14
    buildingCode["Chantier Spatial"           ] = 21
    buildingCode["Hangar de Métal"            ] = 22
    buildingCode["Hangar de Cristal"          ] = 23
    buildingCode["Réservoir de Deutérium"     ] = 24
    buildingCode["Laboratoire de Recherche"   ] = 31
    buildingCode["Dépôt d'Alliance"           ] = 34

    def __init__(self, type, id, planet, level=0):
        self.type = type
        self.level = level
        self.planet = planet
        self.id = id
        if id is None: #if the building isn't upgradable
            self.id = Building.buildingCode[type]
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
            if crystalMine > deutMine + 3:
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
            t[2] = 0 #à remplacer par infini lorsque cette fonction pourra construire des batiments nécéssitant du deut
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

    def expectedRessources(self, timeTarget=time.time(), takeStorageInAccount=True):
        t = (timeTarget - self.lastExtracedInfosDate) / 3600
        em = self.metal + self.metalProduction * t
        ec = self.crystal + self.crystalProduction * t
        ed = self.deut + self.deutProduction * t
        if (takeStorageInAccount):
            return [min(em, self.metalStorage), min(ec, self.crystalStorage), min(ed, self.deutStorage)] 
        return [em, ec, ed]

class Fleet:
    def __init__(self, player, id, origin, target, eta, type):
        self.player = player
        self.id = id
        self.origin = origin
        self.target = target
        self.eta = eta
        self.isGoing = True #either is going to target, or is coming back
        self.type = type
    
    def isHostile(self):
        return self.type == "attack"

class Player:
    def __init__(self, pseudo, mdp, universe, ia):
        self.pseudo = pseudo
        self.mdp = mdp
        self.universe = universe
        self.darkMatter = None
        self.lastRequest = None
        self.lastExtracedInfosDate = None
        self.planets = []
        self.fleets = [] #friendly, own and hostile
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
                    pl = Planet(p.attrs['value'], planet[0][0], [int(x) for x in planet[0][1].split(":")], self)
                    self.planets.append(pl)
                    pl.scan()
    
    def getFleets(self):
        overviewRequest = Request(overviewPage, {})
        self.ia.execRequest(overviewRequest)
        soup = BeautifulSoup(overviewRequest.response.content, "html.parser")
        #parse all available buildings
        fleetsTd = soup.find_all("td", class_="fleets")
        for fleetTd in fleetsTd:
            id = fleetTd.id
            eta = fleetTd.attrs["data-fleet-end-time"]
            fleetSpan = fleetTd.parent.find("span")
            typeList = fleetSpan.attrs["class"]
            isGoing = (typeList[0] == "flight")
            type = typeList[1]
            originA = fleetSpan.findAll("a", class_=type)[1]
            targetA = fleetSpan.findAll("a", class_=type)[2]
            origin = [int(x) for x in originA.text[1:-1].split(":")]
            originIsMoon = "Lune" in originA.previous
            target = [int(x) for x in targetA.text[1:-1].split(":")]
            targetIsMoon = "Lune" in targetA.previous
            fleet = Fleet(self, id, origin, target, eta, type)
            self.fleets.append(fleet)
            originPlanet = self.getOwnPlanetByPosition(origin, originIsMoon)
            targetPlanet = self.getOwnPlanetByPosition(target, targetIsMoon)
            if type == "attack" and targetPlanet is not None and isGoing: #if we are getting attacked
                True #TODO : add task to evade attack fleet
            
            
    def getOwnPlanetByPosition(self, position, isMoon=False):
        for p in self.planets:
            if p.pos == position and p.isMoon == isMoon:
                return p
        return None
        