from bs4 import BeautifulSoup

class CombatReport:

    def __init__(self, combatResult, stolenRessources, loss, debrisField, moonProbability, moonFormed):
        self.combatResult = combatResult #1 if attacker won, -1 if defender won, 0 in a tie
        self.stolenRessources = stolenRessources #the ressources stolen by the attacker
        self.loss = loss #the ressources destroyed in the fight
        self.debrisField = debrisField #the ressources in the debris field
        self.moonProbability = moonProbability #the probability in % of a moon forming
        self.moonFormed = moonFormed #if a moon formed

    def analyzeCombatReport(string):
        soup = BeautifulSoup(string, "html.parser")
        lastTable = soup.find(id="content").div.find_all("table", recursive=False)[-1]

        combatResultElement = lastTable.nextSibling.nextSibling.nextSibling
        combatResultString = str(combatResultElement)
        combatResult = ("attaquant" in combatResultString) - ("défenseur" in combatResultString) #1/0/-1

        stolenRessources = [0, 0, 0]
        if combatResult == 1: #then we have stolen ressources
            stolenRessourcesElement = combatResultElement.nextSibling.nextSibling
            stolenRessourcesString = str(stolenRessourcesElement)
            stolenMetal = int(stolenRessourcesString.split(" a ")[1].split(" Métal")[0].replace(".", ""))
            stolenCrystal = int(stolenRessourcesString.split(", ")[1].split(" Crystal")[0].replace(".", ""))
            stolenDeut = int(stolenRessourcesString.split("Et ")[1].split(" Deut")[0].replace(".", ""))
            stolenRessources = [stolenMetal, stolenCrystal, stolenDeut]
            combatResultElement = stolenRessourcesElement #to continue the next line

        attackerLossElement = combatResultElement.nextSibling.nextSibling.nextSibling
        attackerLossString = str(attackerLossElement).split(" : ")[1].split(" ")[0]
        attackerLoss = int(attackerLossString.replace(".", ""))

        defenderLossElement = attackerLossElement.nextSibling.nextSibling
        defenderLossString = str(defenderLossElement).split(" : ")[1].split(" ")[0]
        defenderLoss = int(defenderLossString.replace(".", ""))

        debrisFieldElement = defenderLossElement.nextSibling.nextSibling
        debrisFieldString = str(debrisFieldElement)
        metalDebrisFieldString = debrisFieldString.split("Débris ")[1].split(" Métal")[0]
        metalDebrisField = int(metalDebrisFieldString.replace(".", ""))
        crystalDebrisFieldString = debrisFieldString.split("Et ")[1].split(" Crystal")[0]
        crystalDebrisField = int(crystalDebrisFieldString.replace(".", ""))

        moonProbabilityElement = debrisFieldElement.nextSibling.nextSibling.nextSibling
        moonProbabilityString = str(moonProbabilityElement)
        moonProbability = int(moonProbabilityString.replace("  ", " ").split(": ")[1].split(" ")[0])

        moonFormedElement = moonProbabilityElement.nextSibling.nextSibling
        moonFormed = moonFormedElement is not None and not "champs" in str(moonFormedElement)

        loss = [attackerLoss, defenderLoss]
        debrisField = [metalDebrisField, crystalDebrisField, 0]
        return CombatReport(combatResult, stolenRessources, loss, debrisField, moonProbability, moonFormed)
