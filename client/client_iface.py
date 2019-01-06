#!/usr/bin/python

import re
import sys
import time
import socket
import threading
from client_code import Client

from kivy.app import App
from kivy.atlas import Atlas
from kivy.lang import Builder
from kivy.uix.gridlayout import GridLayout
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.popup import Popup
from kivy.core.window import Window
from kivy.config import Config

Config.set('input', 'mouse', 'mouse,multitouch_on_demand')
Window.clearcolor = (.66, .38, .78, 1)

in_window_x, in_window_y = 500, 270
co_window_x, co_window_y = 1000, 800
Window.size = (in_window_x, in_window_y)

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client = manager = None
main_check = False

def quit():
    global client, sock, manager
    if sock:
        client.say('quit')
        sock.close()
    Window.close()
    App.get_running_app.close()
    sys.exit(0)

class ButtonPair(GridLayout):
    pass

class UpDownBox(GridLayout):
    def _up(self):
        self.ids['box_val'].text = str(int(self.ids['box_val'].text) + 1)

    def _down(self):
        self.ids['box_val'].text = str(int(self.ids['box_val'].text) - 1)

class TextBoxAndField(GridLayout):
    pass

class InputScreen(Screen):
    def __init__(self, **kwargs):
        super(InputScreen, self).__init__(**kwargs)
        self.sock_conn = False
        self.window_x, self.window_y = in_window_x, in_window_y

    def _okay(self):
        global client, manager, sock, main_check

        self.ids['err_box'].text = ''

        address = self.ids['addr_box'].ids['box_val'].text
        port = self.ids['port_box'].ids['box_val'].text
        username = self.ids['username_box'].ids['box_val'].text
        password = self.ids['password_box'].ids['box_val'].text

        if not self.sock_conn:
            try:
                sock.connect((address, int(port)))
                client = Client(sock)
            except ConnectionRefusedError as msg:
                self.ids['err_box'].text = 'Connection failed: {0}'.format(msg)
                print('Conn fail')
                # Log something probably
                return

        self.sock_conn = True

        cont, ret_str = client.check_credentials(password, username)

        if not cont:
            if ret_str == 'password':
                self.ids['err_box'].text = 'Password incorrect'
            else:
                self.ids['err_box'].text = 'Username already in use'
            return

        manager.next_screen()

        main_check = True

    def _reset(self):
        self.ids['addr_box'].ids['box_val'].text = 'localhost'
        self.ids['port_box'].ids['box_val'].text = '8090'
        self.ids['username_box'].ids['box_val'].text = self.ids['password_box'].ids['box_val'].text = ''

class MainScreen(Screen):
    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        self.window_x, self.window_y = co_window_x, co_window_y
        self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        self._keyboard.bind(on_key_down = self._on_keyboard_down)

        self.thr = threading.Thread(target = self.read_loop)
        self.thr.daemon = True
        self.thr.start()

    def read_loop(self):
        global client, main_check

        while not main_check:
            pass

        self.ids['roll_box'].focus = True

        while True:
            self.ids['msg_box'].text += '\n' + client.handle_read() + '\n----------------------------------------------'

    def _submit(self):
        roll_string = self.ids['n_dice'].ids['box_val'].text + 'd' + self.ids['n_sides'].ids['box_val'].text
        mods = self.ids['mods'].ids['box_val'].text
        if not mods.startswith('-'):
            mods = '+' + mods
        roll_string += mods

        client.say_roll(roll_string)
        self.ids['n_dice'].ids['box_val'].text = '1'
        self.ids['n_sides'].ids['box_val'].text = '20'
        self.ids['mods'].ids['box_val'].text = '0'
        self.ids['roll_box'].focus = True
        

    def _keyboard_closed(self):
        print('Keyboard lost')
        # self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        # self._keyboard = None

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        global main_check, client

        if main_check:
            if self.ids['msg_box'].focus:
                self.ids['roll_box'].focus = True

            if keycode[1] == 'enter': # :enter
                message = self.ids['roll_box'].text
                print(message)
                if re.match(r'^[Qq].*', message):
                    self.thr.join()
                    quit()

                client.say_roll(self.ids['roll_box'].text)
                self.ids['roll_box'].text = ''
                self.ids['roll_box'].focus = True

class Manager(ScreenManager):
    def next_screen(self):
        self.current = 'main'
        Window.size = (co_window_x, co_window_y)

class main_app(App):
    def on_stop(self):
        quit()

    def build(self):
        global manager

        self.root = Builder.load_file('client_iface.kv')
        self.title = 'Python Dice Roller'
        manager = Manager()
        return manager

if __name__ == '__main__':
    main_app().run()
