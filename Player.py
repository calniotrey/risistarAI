import sys
import time
from math import sqrt
from bs4 import BeautifulSoup
from Codes import Codes
from Fleet import Fleet
from Officer import Officer
from OfficersPickingOrder import OfficersPickingOrder
from TechsPickingOrder import TechsPickingOrder
from Planet import Planet
from Request import Request
from Technology import Technology
from UtilitiesFunctions import log

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
        self.officers = {}
        self.techs = {}
        self.researchEnd = 0
        self.ia = ia
        self.officersPickingOrder = None
        self.techsPickingOrder = None
        if ia.config.activatePickingOfficers:
            self.officersPickingOrder = OfficersPickingOrder(filePath=ia.config.officersPickingOrderFile)
        if ia.config.activateAutoResearch:
            self.techsPickingOrder = TechsPickingOrder(filePath=ia.config.techsPickingOrderFile)

    def connexion(self):
        payload = {
            'username' : self.pseudo,
            'password' : self.mdp,
            'universe' : self.universe,
        }
        connexionRequest = Request(self.ia.mainURL + 'page=login', payload)
        connexionRequest.connect(self.ia.session)
        self.lastRequest = connexionRequest
        if """var loginError = "Combinaison login""" in connexionRequest.content:
            log(None, "Login/Password incorrect", isError=True)
            sys.exit("Login/Password incorrect")
        elif """var loginError = "Votre session a expir""" in connexionRequest.content:
            #if the cookie we setup was false
            log(None, "Bad Cookie. Clearing session cookies and trying to reconnect using credentials")
            self.ia.session.cookies.clear()
            self.connexion()
        else:
            log(None, "Connected")
            log(None, "Cookie : @2Moons = " + self.ia.session.cookies["2Moons"])

    def extractInfos(self, request=None, darkMatter=False, planets=True):
        if request == None:
            request = self.lastRequest
        if (request.response != None):
            content = request.content
            soup = BeautifulSoup(content, "html.parser")
            if darkMatter:
                self.darkMatter = int(soup.find(id="current_darkmatter").attrs['data-real'])
                self.lastExtracedInfosDate = time.time()
            if planets:
                ps = soup.find(id="planetSelector").find_all("option")
                self.planets = []
                for p in ps:
                    planet = self.ia.planetNameParser.findall(str(p))
                    id = int(p.attrs['value'])
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
        techEspionage = self.techs.get(106, None)
        techEspionageLevel = 0
        if techEspionage is not None:
            techEspionageLevel = techEspionage.level
        fleets = {}
        overviewRequest = Request(self.ia.overviewPage, {})
        self.ia.execRequest(overviewRequest)
        soup = BeautifulSoup(overviewRequest.response.content, "html.parser")
        #parse all available buildings
        fleetsTd = soup.find_all("td", class_="fleets")
        for fleetTd in fleetsTd[::-1]: #invert the list so the smallest eta overrides the latest
            etaStr = fleetTd.attrs["data-fleet-end-time"]
            eta = float(etaStr)
            id = fleetTd.attrs["id"].split(etaStr)[1] #The etaStr is appended at the end of the id
            secondTd = fleetTd.parent.findAll("td")[1]
            fleetsSpans = secondTd.findAll("span", recursive=False) #can be more than 1 if grouped attack
            typeList = fleetsSpans[-1].attrs["class"] #the last one has the type
            isGoing = (typeList[0] == "flight")
            type = typeList[1]
            aList = fleetsSpans[-1].findAll("a", class_=type)
            ships = {}
            for fleetSpan in fleetsSpans:
                shipsA = fleetSpan.find("a", class_="tooltip")
                if shipsA is not None and techEspionageLevel >= 8:
                    shipsSoup = BeautifulSoup(shipsA.attrs["data-tooltip-content"], "html.parser")
                    for tr in shipsSoup.findAll("tr"):
                        tds = tr.findAll("td")
                        shipType = Codes.strToId[tds[0].text[:-1]]
                        shipAmount = int(tds[1].text.replace(".", ""))
                        ships[shipType] = ships.get(shipType, 0) + shipAmount
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
            fleet = Fleet(self, id, ships, origin, target, eta, type, isGoing)
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

    def getOwnPlanetsByName(self, name):
        res = []
        for p in self.planets:
            if p.name == name:
                res.append(p)
        return res

    def scanTechs(self):
        level, planet = self.getPlanetsWithBuildingOrderedByLevel(31)[0]
        techRequest = Request(self.ia.researchPage + "&cp=" + str(planet.id), {})
        self.ia.execRequest(techRequest)
        self.scanTechsUsingRequest(techRequest)

    def scanTechsUsingRequest(self, techRequest):
        content = techRequest.content
        content = content.replace(")</a></div>", ")</div>") #the site is broken here
        content = content.replace("></a></div>", "></div>")
        soup = BeautifulSoup(content, "html.parser")
        #parse all available techs
        techs = soup.find(id="content").find_all("div", recursive=False)
        self.techs = {}
        self.researchEnd = 0
        for r in techs:
            if r.attrs.get("id") == "buildlist": #if it's a techs being currently researched
                self.researchEnd = float(r.find(class_="timer").attrs["data-time"]) #at the end of the loop, it will be the end of the last tech
            else:
                nameElement = r.find("a")
                name = nameElement.text
                level = 0
                if nameElement.nextSibling is not None:
                    levelString = str(nameElement.nextSibling) # (Niveau 9) for example
                    level = int(levelString.split("Niveau ")[1].split(")")[0])
                divs = r.find_all("div", recursive=False)
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
                for r in self.ia.ressourcesParser.findall(costText):
                    if r[1] == "Metal":
                        res[0] = int(r[0])
                    if r[1] == "Crystal":
                        res[1] = int(r[0])
                    if r[1] == "Deut":
                        res[2] = int(r[0])
                form = divs[3].find("input", attrs={"name": "tech"})
                id = Codes.strToId.get(name)
                if form != None and id == None:
                    id = form.attrs['value']
                tech = Technology(name, id, self, level)
                tech.upgradeCost = res
                tech.upgradeTime = upgradeTime
                self.techs[id] = tech

    def scanOfficers(self):
        officerRequest = Request(self.ia.officerPage, {})
        self.ia.execRequest(officerRequest)
        self.officers = Officer.getOfficersUsingLastRequest(self)

    def chooseOfficerToPick(self): #doesn't check if enough DM
        return self.officersPickingOrder.nextOfficer(self.officers)

    def chooseTechToPick(self):
        log(None, "Planning tech to research")
        techId = None
        if self.techsPickingOrder is not None:
            tech = self.techsPickingOrder.nextTech(self.techs) # the tech to research
            if tech is None:
                if self.techsPickingOrder.options.get("useDefaultTechPlanWhenEmpty", False):
                    tech = self.chooseTechToPickByDefault()
                else:
                    log(self, "No more techs planned by the technology picking order !")
                    return None
        else:
            tech = self.chooseTechToPickByDefault()
        if tech is not None:
            # Now we need to find a suitable planet to research it
            level, planet = self.getPlanetsWithBuildingOrderedByLevel(31)[0] # The planet with highest lab
            return tech, planet

    def chooseTechToPickByDefault(self):
        """The logic is the following : astrophysic when astro.cost < 4 * computer.cost, else computer"""
        tech = None
        astro = self.techs.get(124, None)
        astroCost = 0
        if astro is not None:
            astroCost = astro.getTotalUpgradeCostWeighted()
        computer = self.techs.get(108, None)
        computerCost = 0
        if computer is not None:
            computerCost = computer.getTotalUpgradeCostWeighted()
        if astroCost < 4 * computerCost:
            if astro is not None:
                return astro
            else:
                return Technology(Codes.idToStr[124], 124, self)
        else:
            if computer is not None:
                return computer
            else:
                return Technology(Codes.idToStr[108], 108, self)

    def checkNewAchievement(self): #returns True if a new achievement was achieved
        checkAchievementRequest = Request(self.ia.achievementsPage, {})
        self.ia.execRequest(checkAchievementRequest)
        soup = BeautifulSoup(checkAchievementRequest.content, "html.parser")
        return soup.find(class_="kategorie") is None

    def getPlanetsWithBuildingOrderedByLevel(self, buildingId, descendingOrder=True):
        list = []
        for planet in self.planets:
            buildingLevel = planet.buildingLevelById(buildingId)
            if buildingLevel > 0:
                list.append((buildingLevel, planet))
        list.sort(key=lambda x:x[0], reverse=descendingOrder)
        return list

    def getMaximumNumberOfPlanets(self):
        astro = self.techs.get(124, None)
        if astro is None:
            return 1
        return (astro.level + 3) // 2

    def getActualNumberOfPlanets(self):
        number = 0
        for planet in self.planets:
            if not planet.isMoon:
                number += 1
        return number

    def getColonizableLocations(self):
        # Returns the colonizable locations in the 'best' order
        astro = self.techs.get(124, None)
        if astro is None:
            return []
        else:
            if astro.level >= 8:
                return [8, 7, 9, 6, 10, 5, 11, 4, 12, 3, 13, 2, 14, 1, 15]
            elif astro.level >= 4:
                return [8, 7, 9, 6, 10, 5, 11, 4, 12, 3, 13, 2, 14]
            elif astro.level >= 2:
                return [8, 7, 9, 6, 10, 5, 11, 4, 12, 3, 13]
            elif astro.level >= 1:
                return [8, 7, 9, 6, 10, 5, 11, 4, 12]
            else:
                return []

    def getMaximumNumberOfExpeditions(self):
        astro = self.techs.get(124, None)
        if astro is None:
            return 0
        return int(sqrt(astro.level))

    def getActualNumberOfExpeditions(self):
        number = 0
        for fleet in self.fleets.values():
            if fleet.isExpedition(): #no need to check if coming back, only one id for both
                number += 1
        return number

    def scanOwnShips(self): # TODO replace this by scraping the empire page
        for planet in self.planets:
            planet.scanShips()
