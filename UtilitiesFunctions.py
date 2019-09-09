import time

def log(planet, str, isError=False):
    if planet != None:
        print(time.strftime("%H:%M:%S"), " [", planet.id, "] ", str, sep='')
    else:
        print(time.strftime("%H:%M:%S"), " [   ] ", str, sep='')
