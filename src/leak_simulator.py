import math
from random import random

def random_walk(value, step,start,end):
    min = start
    max = end

    if random() >= 0.5:
        value += step
    else:
        value -= step

    if(value > max ):
        value = max
    if(value < min):
        value = min

    return value

def simulate(method,value, step,start,end,parameters=[],path=''):
    if method=='random_walk':
        value=random_walk(value, step,start,end)
    return value
