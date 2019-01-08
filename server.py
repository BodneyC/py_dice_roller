#!/usr/bin/python

import sys, errno
import socket
import logging
from threading import Thread

from dice_roller import roll as dice_roll

BUF_SIZE = 1024

class RClient:
    def __init__(self, username, conn, host):
        self.username = username
        self.conn = conn
        self.host = host

    def get_username(self):
        return self.username

    def get_conn(self):
        return self.conn

class Server:
    log = logging.getLogger('Server')

    def __init__(self, address = ('localhost', 8090), password = 'fish'):
        self.log.info(' Server started on: {0}\n     Password is: {1}'.format(address, password))

        self.password = password
        self.remote_clients = {}
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(address)
        self.sock.listen(1)

        self.run_loop()

    def run_loop(self):
        thr_pool = []
        while True:
            try:
                conn, addr = self.sock.accept()
            except socket.timeout:
                continue
            tmpThr = Thread(target = self.handle_accept, args=[conn, addr])
            tmpThr.daemon = True
            print('CON X')
            tmpThr.start()
            thr_pool.append(tmpThr)
            # Check for dead conns
            # Break for something

        for thr in thr_pool:
            thr.join()

    # Loop threads on this
    def handle_accept(self, conn, addr):
        self.log.info('Accepted client at %s', addr)

        while True:
            # Put error onto `conn`
            try:
                if self.check_connection(conn) and self.check_connection(conn):
                    break
            except (socket.error, socket.timeout) as e:
                conn = None
                self.log.warn(e)
                break

        if conn:
            rclient = self.remote_clients[conn.recv(BUF_SIZE).decode()]
            self.begin_rolling(rclient)

    def format_string(self, message):
        message = message.replace(' ', '')
        message = message.replace('+', ' + ')
        message = message.replace('-', ' - ')
        return message

    def begin_rolling(self, rclient):
        while True:
            try:
                line = rclient.conn.recv(BUF_SIZE).decode()
            except (socket.error, socket.timeout, ConnectionResetError) as e:
                self.log.warn(e)
                del self.remote_clients[rclient.username]
                return
            
            if line.startswith('q') or line.startswith('Q'):
                self.log.info('User \'{0}\' left'.format(rclient.username))
                del self.remote_clients[rclient.username]
                return

            roll_info = dice_roll(line[5:])
            roll_list = self.format_string(line[5:])

            put_string = rclient.get_username() + ':\n    ' + roll_list + '\n    ' + roll_info

            if roll_info.startswith('Invalid'):
                try:
                    rclient.get_conn().sendall(put_string)
                except socket.error as e:
                    self.log.warn(e)
                    del self.remote_clients[rclient.username]
                    return
            else:
                self.log.info('Message {0}'.format(put_string))
                self.broadcast(put_string)

    # Errors catch in self.handle_accept()
    def check_connection(self, conn):
        client_message = conn.recv(BUF_SIZE).decode()

        if client_message.startswith('PSWD:'):
            pswd_succ = int(client_message[5:] == self.password)
            if pswd_succ:
                self.log.info('Connection {0}: Password accepted'.format(conn))
            conn.sendall(str(pswd_succ).encode())
            return pswd_succ

        if client_message.startswith('USER:'):
            username = client_message[5:]
            if username in self.remote_clients.keys():
                conn.sendall('0'.encode())
                self.log.warn('Connection {0}: Username not accepted'.format(conn))
                return False
            self.log.info('Connection {0}: Username accepted'.format(conn))
            self.remote_clients[username] = RClient(username, conn, self)
            conn.sendall('1'.encode())
            return True

        return False

    def broadcast(self, message):
        self.log.info('Broadcasting message:\n%s', message)
        for rc_username in self.remote_clients:
            if self.remote_clients[rc_username]:
                try:
                    self.remote_clients[rc_username].get_conn().sendall(message.encode())
                except IOError as msg:
                    self.log.warn('User \'{0}\' left unexpectedly\n  {1}'.format(rc_username, msg))
                    del self.remote_clients[rc_username]

if __name__ == '__main__':
    socket.setdefaulttimeout(100)
    logging.basicConfig(level = logging.INFO)

    sock_addr, sock_port, password = 'localhost', 8090, ''

    show_help = 'Usage\n\t./server.rb [<address> <port> [<password]]'

    if '-h' in sys.argv or '--help' in sys.argv:
        print(show_help)
        quit()

    argv = sys.argv[1:]
    if len(argv) >= 2:
        sock_addr, sock_port = argv[0], int(argv[1])
    if len(argv) == 3:
        pswd = argv[2]

    Server((sock_addr, sock_port), password)
