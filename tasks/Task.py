class Task:
    highPrio   = 0
    middlePrio = 1
    lowPrio    = 2
    descendingPrio = [highPrio, middlePrio, lowPrio]

    def __init__(self, t):
        self.t = t
        self.prio = Task.lowPrio

    def __gt__(self, other):
        return self.t > other.t

    def __ge__(self, other):
        return self.t >= other.t
