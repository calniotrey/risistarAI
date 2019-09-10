import time
from Officer import Officer
from tasks.Task import Task
from UtilitiesFunctions import log

class PickOfficerTask(Task):
    def __init__(self, t, player):
        self.t = t
        self.player = player
        self.prio = Task.lowPrio

    def execute(self):
        self.player.scanOfficers()
        officer = self.player.chooseOfficerToPick()
        if officer is not None and self.player.darkMatter >= 1000:
            log(None, "Upgrading the officer " + officer.type)
            req = officer.upgrade()
            self.player.extractInfos(request=req, darkMatter=True, planets=False)
            if self.player.darkMatter >= 1000:
                newTask = PickOfficerTask(time.time(), self.player)
                self.player.ia.addTask(newTask)
