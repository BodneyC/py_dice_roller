#!/usr/bin/python

import re
import sys, os
import time
import socket
import threading
from client_code import Client

from kivy.resources import kivy
from kivy.app import App
from kivy.atlas import Atlas
from kivy.lang import Builder
from kivy.uix.gridlayout import GridLayout
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.popup import Popup
from kivy.core.window import Window
from kivy.config import Config

kivy.require('1.10.1')

Config.set('input', 'mouse', 'mouse,multitouch_on_demand')
Window.clearcolor = (.27, .29, .3, 1)

in_window_x, in_window_y = 550, 270
co_window_x, co_window_y = 1000, 800
Window.size = (in_window_x, in_window_y)

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client = manager = None
main_check = False

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
        self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        self._keyboard.bind(on_key_down = self._on_keyboard_down)

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
                self.ids['err_box'].text = 'Connection failed: Server refused'
                print('Connection failed: {0}'.format(msg))
                # Log something probably
                return

        self.sock_conn = True

        if username == '':
            self.ids['err_box'].text = 'Please provide a username'
            return

        cont, ret_str = client.check_credentials(password, username)

        if not cont:
            if ret_str == 'password':
                self.ids['err_box'].text = 'Password incorrect'
            else:
                self.ids['err_box'].text = 'Username already in use'
            return

        manager.next_screen()

        self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        self._keyboard = None
        main_check = True

    def _reset(self):
        self.ids['addr_box'].ids['box_val'].text = 'localhost'
        self.ids['port_box'].ids['box_val'].text = '8090'
        self.ids['username_box'].ids['box_val'].text = self.ids['password_box'].ids['box_val'].text = ''

    def _keyboard_closed(self):
        pass

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        if keycode[1] == 'enter':
            self._okay()
        



class MainScreen(Screen):
    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        self.window_x, self.window_y = co_window_x, co_window_y
        self._keyboard = None
        self.msg_hist = []
        self.hist_n = 0

        self.thr = threading.Thread(target = self.read_loop)
        self.thr.daemon = True
        self.thr.start()

    def read_loop(self):
        global client, main_check

        while not main_check:
            time.sleep(1)

        self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        self._keyboard.bind(on_key_down = self._on_keyboard_down)

        self.ids['roll_box'].focus = True

        while True:
            self.ids['msg_box'].text += '\n' + client.handle_read() + '\n----------------------------------------------'

    def _submit(self):
        if self.ids['roll_box'].text != '':
            self.text_roll()
            return

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

    def _clear_roll_box(self):
        self.ids['roll_box'].text = ''

    def _keyboard_closed(self):
        pass

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        if self.ids['msg_box'].focus:
            self.ids['roll_box'].focus = True

        if keycode[1] == 'enter': # :enter
            self.hist_n = 0
            self.ids['roll_box'].focus = True
            self.msg_hist.append(self.ids['roll_box'].text)
            self.text_roll()
            return

        if self.ids['roll_box'].focus:
            if modifiers and modifiers[0] == 'ctrl' and keycode[1] == 'backspace':
                if self.ids['roll_box'].text.__contains__(' '):
                    self.ids['roll_box'].text = self.ids['roll_box'].text.rsplit(' ', 1)[0]
                else:
                    self.ids['roll_box'].text = ''
            elif keycode[1] == 'up':
                if len(self.msg_hist) > self.hist_n:
                    self.hist_n += 1
                    self.ids['roll_box'].text = self.msg_hist[-self.hist_n]
            elif keycode[1] == 'down':
                if self.hist_n != 0:
                    self.hist_n -= 1
                    self.ids['roll_box'].text = self.msg_hist[-self.hist_n]
                else:
                    self.ids['roll_box'].text = ''

    def text_roll(self):
        global client

        message = self.ids['roll_box'].text
        print(message)

        client.say_roll(self.ids['roll_box'].text)
        self.ids['roll_box'].focus = True

class Manager(ScreenManager):
    def next_screen(self):
        self.current = 'main'
        Window.size = (co_window_x, co_window_y)

class main_app(App):
    def on_stop(self):
        quit_app()

    def build(self):
        global manager

        self.root = Builder.load_file('client_iface.kv')
        self.title = 'Python Dice Roller'
        manager = Manager()
        return manager

def quit_app():
    global client, sock, manager
    if client:
        client.say('quit')
        sock.close()
    Window.close()
    sys.exit(0)

def resourcePath(path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS)

    return os.path.join(os.path.abspath(path))

if __name__ == '__main__':
    kivy.resources.resource_add_path(resourcePath('.'))
    kivy.resources.resource_add_path(resourcePath('./images'))
    kivy.resources.resource_add_path(resourcePath('./fonts'))
    # kivy.resources.resource_add_path(resourcePath('D:/Users/BenJC/AppData/Local/Programs/Python/Python36/lib/site-packages'))
    # kivy.resources.resource_add_path(resourcePath('D:/Users/BenJC/AppData/Local/Programs/Python/Python36/lib/site-packages/core'))
    main_app().run()
