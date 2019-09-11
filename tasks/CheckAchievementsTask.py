import time
from tasks.Task import Task
from tasks.PlanningTask import PlanningTask
from UtilitiesFunctions import log

class CheckAchievementsTask(Task):
    def __init__(self, t, player):
        self.t = t
        self.player = player
        self.prio = Task.lowPrio

    def execute(self):
        log(None, "Checking achievements")
        hadNewAchievement = self.player.checkNewAchievement()
        if hadNewAchievement:
            log(None, "Just got an achievement!")
            newTask = CheckAchievementsTask(time.time(), self.player)
            self.player.ia.addTask(newTask)
        else:
            log(None, "No new achievement")
