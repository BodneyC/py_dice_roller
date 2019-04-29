#!/usr/bin/python

import sys, errno
import socket
import logging
import datetime
from threading import Thread
from argparse import ArgumentParser

import dnd_dice_roller
import sr_dice_roller

BUF_SIZE = 1024

log_file = './server_logs/' + datetime.datetime.now().strftime("%I:%M%p-%y-%m-%d") + '.log'
logging.FileHandler(log_file, mode = 'a', encoding = None, delay = False)
logging.basicConfig(filename = log_file, level = logging.INFO)
logging.getLogger().addHandler(logging.StreamHandler())

class RClient:
    def __init__(self, username, conn, host):
        self.username = username
        self.nickname = username
        self.conn = conn
        self.host = host

    def set_nickname(self, nickname):
        self.nickname = nickname

    def get_conn(self):
        return self.conn

class Server:
    log = logging.getLogger('Server')

    def __init__(self, address, game_type, password):
        self.address = address
        self.game_type = game_type
        self.password = password
        self.remote_clients = {}
        self.dice_roll = None
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.settimeout(None)

    def start_server(self):
        if self.game_type == 'dungeons':
            self.dice_roll = dnd_dice_roller.roll
        elif self.game_type == 'shadowrun':
            self.dice_roll = sr_dice_roller.roll
        else:
            self.log.error(f'{self.game_type} not accepted game type, exiting...')
            return False
        try:
            self.sock.bind(self.address)
        except PermissionError:
            self.log.error(f'Cannot bind to {self.address}, exiting...')
            return False
        self.sock.listen(1)
        self.log.info(f'Server started on: {self.address}\n     Password is: {self.password}')

        try:
            self.run_loop()
        except (KeyboardInterrupt, EOFError):
            self.log.error('Keyboard interrupt')
            return True
        except Exception:
            return False

    def run_loop(self):
        thr_pool = []
        while True:
            try:
                conn, addr = self.sock.accept()
            except socket.timeout:
                continue
            tmpThr = Thread(target = self.handle_accept, args=[conn, addr])
            tmpThr.daemon = True
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
            self.log.info('Connection {0}: Username \'{1}\' accepted'.format(conn, username))
            self.remote_clients[username] = RClient(username, conn, self)
            conn.sendall('1'.encode())
            return True

        return False

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

            if line.startswith('ROLL:/'): # Command
                if line[5:].startswith('/nick'):
                    rclient.set_nickname(line.split(' ', 1)[1])
                    put_string = 'Nickname chaged to \'' + rclient.nickname + '\''
                    self.send_one(rclient.username, put_string)

                elif line[5:].startswith('/pm'):
                    pm_info = line[5:].split(' ', 2)[1:]
                    put_string = self._name_string(rclient) + ' (PM)\n    ' + pm_info[1]
                    if pm_info[0] in self.remote_clients.keys():
                        if self.send_one(pm_info[0], put_string):
                            put_string = 'Message sent to \'' + pm_info[0] + '\''
                            self.send_one(rclient.username, put_string)
                        else:
                            self.send_one(rclient.username, 'Username \'{0}\' failed to recieve message'.format(pm_info[0]))
                    else:
                        self.send_one(rclient.username, 'Username \'{0}\' does not exist'.format(pm_info[0]))

                continue

            roll_info = self.dice_roll(line[5:])
            if self.game_type in ('dungeons'):
                roll_list = self.format_string(line[5:])
            else:
                roll_list = line[5:]

            put_string = self._name_string(rclient) + '\n    ' + roll_list + '\n    ' + roll_info

            if roll_info.startswith('Invalid'):
                try:
                    rclient.get_conn().sendall(put_string.encode())
                except socket.error as e:
                    self.log.warn(e)
                    del self.remote_clients[rclient.username]
                    return
            else:
                self.log.info('Message\n\'{0}\''.format(put_string))
                self.broadcast(put_string)

    def _name_string(self, rclient):
        if rclient.username == rclient.nickname:
            return rclient.username
        else:
            return rclient.username + ' \'' + rclient.nickname + '\' '

    def format_string(self, message):
        message = message.replace(' ', '')
        message = message.replace('+', ' + ')
        message = message.replace('-', ' - ')
        return message

    def send_one(self, username, message):
        try:
            self.remote_clients[username].get_conn().sendall(message.encode())
        except (IOError, socket.error) as msg:
            self.log.warn('User \'{0}\' unable to recieve, deleting\n {1}'.format(username, msg))
            del self.remote_clients[username]
            return False
        return True

    def broadcast(self, message):
        self.log.info('Broadcasting message:\n%s', message)
        for rc_username in self.remote_clients:
            print("Broadacsting")
            if self.remote_clients[rc_username]:
                self.send_one(rc_username, message)

def parse_args():
    parser = ArgumentParser()
    parser.add_argument('-a', '--address', default='localhost')
    parser.add_argument('-p', '--port', default=8090, type=int)
    parser.add_argument('--pswd', '--password', default='')
    parser.add_argument('-t', '--game_type', default='dungeons')
    return parser.parse_args()

def main():
    args = parse_args()
    server = Server((args.address, args.port), args.game_type, args.pswd)
    if not server.start_server():
        sys.exit(1)

if __name__ == '__main__':
    main()

