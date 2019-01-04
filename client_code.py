#!/usr/bin/python

import sys
import socket
import logging
import threading

import time

BUF_SIZE = 1024

class Client:

    def __init__(self, sock):
        self.sock = sock
        self.textbox = []

    def check_credentials(self, password, username):
        self.say("PSWD:" + password)
        # print(self.sock.recv(BUF_SIZE))
        if not int(self.sock.recv(BUF_SIZE).decode()):
            return False

        self.say("USER:" + username)
        # print(self.sock.recv(BUF_SIZE))
        if not int(self.sock.recv(BUF_SIZE).decode()):
            return False

        self.say(username)

        return True

    def say_roll(self, message):
        self.say("ROLL:" + message)

    def say(self, message):
        if len(message) > BUF_SIZE:
            raise ValueError('Message too long')
        self.sock.sendall(message.encode())

    def handle_read(self):
        while True:
            message = self.sock.recv(BUF_SIZE).decode()
            self.textbox.append(message.split("\n"))
            print(message)
            
if __name__ == "__main__":
    sock_addr, sock_port, pswd = "localhost", 8090, ""

    show_help = "Usage\n\t./client.rb [<address> <port> [<password>]]"

    if "-h" in sys.argv or "--help" in sys.argv:
        print(show_help)
        quit()

    argv = sys.argv[1:]
    if len(argv) >= 2:
        sock_addr, sock_port = argv[0], argv[1]
    if len(argv) == 3:
        pswd = argv[2]

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    while True:
        try:
            sock.connect((sock_addr, int(sock_port)))
            break
        except ConnectionRefusedError as msg:
            print("Connection failed, retry...")
            print(msg)
        sock_addr, sock_port = input("Address: "), input("Port: ")

    print("Connected successfully...")
    client = Client(sock)

    while True:
        password, username = input("Password: "), input("Username: ")
        if client.check_credentials(password, username):
            break

    thr = threading.Thread(target = client.handle_read, args = ())
    thr.daemon = False
    thr.start()

    while True:
        line = input("Roll: ")
        if line.startswith("q"):
            break
        client.say_roll(line)

    thr.join()
