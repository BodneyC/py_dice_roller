#!/usr/bin/python

import re
import sys
import random

def roll_dice(dice_num=0, sides=6):
    lows = 0
    highs = 0
    vals = []

    for i in range(0, dice_num):
        vals.append(random.randint(1, sides))
        if vals[i] in (5, 6):
            highs += 1
        if vals[i] is 1:
            lows += 1

    return lows, highs, vals

def roll(dice_num):
    dice_num = dice_num.replace(' ', '')

    if not dice_num.isdigit():
        return 'Invalid request'

    dice_num = int(dice_num)

    lows, highs, roll_vals = roll_dice(dice_num)

    out_string = '\nRolls: ' + str(roll_vals)

    if lows >= dice_num / 2:
        out_string += f'\n\n{lows}/{dice_num} ones: Crit fail\n'
    else:
        out_string += f'\n\n{highs} fives and sixes\n'

    return out_string

def main(line):
    line = ''
    for i in range(1, len(sys.argv)):
        line += sys.argv[i]
    print(roll(line))

if __name__ == '__main__':
    main(sys.argv)
