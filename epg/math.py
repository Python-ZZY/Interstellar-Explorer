from pygame.math import *

def counter(start=0, stop=None, step=1):
    '''Count from [start=0] to [stop=None]'''
    if not stop:
        while True:
            yield start
            start += step
    else:
        yield from range(start, stop, step)

def mix(a, b, pos, key=lerp):
    try:
        return key(a, b, pos)
    except TypeError:
        return [key(a[i], b[i], pos) for i in range(len(a))]

def round_to_int(x):
    i = int(x)
    return i if x - i < 0.5 else i + 1

def num(number, ndigits=None):
    if ndigits:
        number = round(number, ndigits)
    return number if number % 1 else int(number)
