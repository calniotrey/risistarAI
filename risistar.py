import requests
import sys, time, re
import heapq
from bs4 import BeautifulSoup

file = open("secret.txt")
pseudo = file.readline().replace("\n", "")
password = file.readline().replace("\n", "")  # en clair
file.close()

mainURL = 'http://risistar.fr/index.php?'
buildingPage = 'http://risistar.fr/game.php?page=buildings'
session = requests.session()

planetNameParser = re.compile(r'''>(.*) \[(.*)\]''')
buildingNameParser = re.compile(r'''\A([^\(]+)(?:\(.* (\d*))?''')
ressourcesParser = re.compile(r'''(\d+) (\w+);''')

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
        self.player = Player(pseudo, password, "Risistar")
        self.player.connexion()
        self.player.extractInfos(planets=True)
        self.h = []
        for p in self.player.planets:
            self.addTask(ScanPlanetTask(time.time(), p))
    
    def addTask(self, t):
        heapq.heappush(self.h, t)
    
    def run(self):
        while len(self.h) and self.h[0].t < time.time():
            taskToExecute = heapq.heappop(self.h)
            taskToExecute.execute()

class BuildingTask(Task):
    def __init__(self, t, bat):
        self.t = t
        self.bat = bat
    
    def execute(self):
        self.bat.upgrade()

class ScanPlanetTask(Task):
    def __init__(self, t, planet):
        self.t = t
        self.planet = planet
    
    def execute(self):
        self.planet.scan()


class Building:
    def __init__(self, type, id, planet, level=0):
        self.type = type
        self.level = level
        self.planet = planet
        self.id = id
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
            reqB.connect()
            self.lastRequest = reqB
        
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
        self.lastExtracedInfosDate = None
    
    def upgradableBuildings(self, ressources):
        return [bat for bat in self.batimens if bat.upgradable(ressources)]
    
    def scan(self):
        reqB = Request(buildingPage + "&cp=" + self.id, {})
        reqB.connect()
        self.player.lastRequest = reqB
        soup = BeautifulSoup(reqB.content, "html.parser")
        bats = soup.find(id="content").find_all("div", recursive=False)
        self.batiments = []
        for b in bats:
            nameAndLevelText = b.find("a").text
            nameAndLevel = buildingNameParser.findall(nameAndLevelText)
            name = nameAndLevel[0][0]
            level = 0
            if nameAndLevel[0][1] != '':
                level = int(nameAndLevel[0][1])
            divs = b.find_all("div", recursive=False)
            upgradeTime = divs[1].span.text
            m = divs[2].span.find(alt="Métal")
            if m != None:
                m.replace_with("Metal;")
            c = divs[2].span.find(alt="Crystal")
            if c != None:
                c.replace_with("Crystal;")
            d = divs[2].span.find(alt="Deutérium")
            if d != None:
                d.replace_with("Deut;")
            costText = divs[2].span.text
            res = [0, 0, 0]
            for r in ressourcesParser.findall(costText):
                if r[1] == "Metal":
                    res[0] = r[0]
                if r[1] == "Crystal":
                    res[1] = r[0]
                if r[1] == "Deut":
                    res[2] = r[0]
            form = divs[4].find("input", attrs={"name": "building"})
            id = None
            if form != None:
                id = form.attrs['value']
            b = Building(name, id, self, level)
            b.upgradeCost = r
            b.upgradeTime = upgradeTime
            self.batiments.append(b)

        self.metal = float(soup.find(id="current_metal").attrs['data-real'])
        self.crystal = float(soup.find(id="current_crystal").attrs['data-real'])
        deutTd = soup.find(id="current_deuterium")
        energySpan = deutTd.nextSibling.span
        
        self.deut = float(deutTd.attrs['data-real'])
        self.metalStorage = float(soup.find(id="max_metal").text.replace(".", ""))
        self.crystalStorage = float(soup.find(id="max_crystal").text.replace(".", ""))
        self.deutStorage = float(soup.find(id="max_deuterium").text.replace(".", ""))
    
    
    def expectedRessources(self, timeTarget=time.time(), takeStorageInAccount=True):
        t = (timeTarget - self.lastExtracedInfosDate) / 3600
        em = self.metal + self.metalProduction * t
        ec = self.crystal + self.crystalProduction * t
        ed = self.deut + self.deutProduction * t
        if (takeStorageInAccount):
            return [min(em, self.metalStorage), min(ec, self.crystalStorage), min(ed, self.deutStorage)] 
        return [em, ec, ed]

class Player:
    def __init__(self, pseudo, mdp, universe):
        self.pseudo = pseudo
        self.mdp = mdp
        self.universe = universe
        self.darkMatter = None
        self.lastRequest = None
        self.lastExtracedInfosDate = None
        self.planets = []
      
    def connexion(self):
        payload = {
            'username' : self.pseudo,
            'password' : self.mdp,
            'universe' : self.universe,
        }
        connexionRequest = Request(mainURL + 'page=login', payload)
        connexionRequest.connect()
        self.lastRequest = connexionRequest

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



def lancer_roulotte():
    pseudo = input()
    mdp = input()
    minutesParser = re.compile("Temps restant avant attaque : (\d*)min")
    secondesParser = re.compile("Temps restant avant attaque : (\d*)sec")
    while True:
        r = attaque_planetaire(pseudo, mdp)
        r = r.content.decode()
        tm = minutesParser.findall(r)
        ts = secondesParser.findall(r)
        if tm != []:
            t = int(tm[0])*60
        elif ts != []:
            t = int(ts[0])+1
        else:
            t = 60*60
        print(t)
        time.sleep(t)

    
    