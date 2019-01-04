Python Dice Roller
================

- Dice roller aimed at RPG tabletops.
- A little TCP server/client combination exists which uses ./dice_roller.py.
- The client will eventually be in a TUI environment (once I find a decide upon a library for it)

### NOTE

This repo is near-identical to [my other one](https://github.com/BodneyC/ruby_dice_roller) but where this one is Python, that one is Ruby.

I originally wanted to make it in Ruby but the TUI libraries are sparse andthe only one I can get working fairly well has little to no Windows support (which is where team-mates will be wanting to use it).

### Usage

Usage currently changes with the two types of program bullet-pointed above:

#### Dice Roller

The roller itself, `dice_roller.py`, can be called from the command line in the format:

    ./dice_roller.py XdY + Z - ...

Spaces "` `" can be placed wherever, modifications `+ Z - ...` are not necessary.

Output is of the form:

    $ ./dice_roller.py 2d20 + 5 - 1
    29 [9 + 16] (+ 5 - 1)

#### Client/Server

Both client and server, `server.py`, and `client_code.py`, can be given an address/port but default to `"localhost"`, `8090`; the server can then be given a password in the form:

	$ ./server [<address> <port> [<password>]]

The clients then provide a username and give roll command in the syntax given above.

