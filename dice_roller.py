#!/usr/bin/python

import re
import sys
import random

def validate(message):
    if re.match("/^\d+?d\d+?([+-]\d+?)*$/", message):
        return 1
    return 0

def roll_dice(die_num = 0, sides = 0):
    total = 0
    vals = []

    for i in range(0, die_num):
        vals.append(random.randint(0, sides))
        total += vals[-1]

    return total, vals

def roll(message):
    message = message.replace(" ", "")

    if validate(message) == 1:
        return "Invalid request"

    # Split on [d+-] and keep
    args = re.split("([d+-])", message)

    # Every other to int
    for i in range(0, len(args), 2):
        args[i] = int(args[i])

    total, roll_vals = roll_dice(args[0], args[2])

    if len(args) > 3:
        for i in range(3, len(args), 2):
            if args[i] == "+":
                total += args[i + 1]
            else:
                total -= args[i + 1]

    out_string = str(total)
    if args[0] > 1:
        out_string += " [" + (" + ").join(str(val) for val in roll_vals) + "]"
    if len(args) > 3:
        out_string += " (" + (" ").join(str(val) for val in args[3:len(args)]) + ")"

    return out_string

if __name__ == "__main__":
    line = ""
    for i in range(1, len(sys.argv)):
        line += sys.argv[i]
    print(roll(line))
