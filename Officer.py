from bs4 import BeautifulSoup
from Codes import Codes
from Request import Request
from UtilitiesFunctions import log

class Officer:
    def __init__(self, type, id, player, level=0):
        self.type = type
        self.level = level
        self.player = player
        self.id = id
        self.darkMatterCost = None

    def upgradable(self, availableDarkMatter):
        return self.darkMatterCost > availableDarkMatter

    def upgrade(self):
        if self.id != None:
            payload = {'id': self.id}
            reqO = Request(self.player.ia.officerPage, payload)
            self.player.ia.execRequest(reqO)
            return reqO

    def getOfficersUsingLastRequest(player):
        content = player.lastRequest.content
        soup = BeautifulSoup(content, "html.parser")
        #parse all officers
        officersDiv = soup.find(id="tab1").find_all("div", recursive=False)
        officers = {}
        for o in officersDiv:
            nameAndLevelText = o.find("a").text
            nameAndLevel = player.ia.buildingNameParser.findall(nameAndLevelText) #works for officers too
            name = nameAndLevel[0][0]
            level = 0
            if nameAndLevel[0][1] != '':
                level = int(nameAndLevel[0][1])
            divs = o.find_all("div", recursive=False)
            dmSpan = divs[2].span.find("span")
            dmRequired = 0
            if dmSpan != None:
                dmRequired = int(dmSpan.text.replace(".", ""))
            form = divs[3].find("input", attrs={"name": "id"})
            id = Codes.strToId.get(name)
            if form != None and id == None:
                id = form.attrs['value']
                if id == None:
                    log(None, "Unknown officer with no id parsed.", isError=True)
            officer = Officer(name, id, player, level)
            officer.darkMatterCost = dmRequired
            officers[id] = officer
        return officers
