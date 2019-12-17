import time

def log(planet, str, isError=False):
    if planet != None:
        print(time.strftime("%H:%M:%S"), " [", planet.id, "] ", str, sep='')
    else:
        print(time.strftime("%H:%M:%S"), " [   ] ", str, sep='')

def is_number(n):
    is_number = True
    try:
        num = float(n)
        # check for "nan" floats
        is_number = num == num   # or use `math.isnan(num)`
    except ValueError:
        is_number = False
    return is_number
