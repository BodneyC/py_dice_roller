#!/usr/bin/python

import re
import sys
import time
import socket
import threading
from client_code import Client

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.gridlayout import GridLayout
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.popup import Popup
from kivy.core.window import Window

in_window_x, in_window_y = 500, 270
co_window_x, co_window_y = 1000, 800
# Should be in_*
Window.size = (in_window_x, in_window_y)

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client = manager = None
main_check = False

class ButtonPair(GridLayout):
    pass
    
class TextBoxAndField(GridLayout):
    pass

class InputScreen(Screen):
    def __init__(self, **kwargs):
        super(InputScreen, self).__init__(**kwargs)
        self.sock_conn = False

    def _okay(self):
        global client, manager, sock, main_check

        self.ids["err_box"].text = ""

        address = self.ids["addr_box"].ids["box_val"].text
        port = self.ids["port_box"].ids["box_val"].text
        username = self.ids["username_box"].ids["box_val"].text
        password = self.ids["password_box"].ids["box_val"].text

        if not self.sock_conn:
            try:
                sock.connect((address, int(port)))
            except ConnectionRefusedError as msg:
                self.ids["err_box"].text = "Connection failed: {0}".format(msg)
                print("Conn fail")
                # Log something probably
                return

        self.sock_conn = True

        client = Client(sock)

        if not client.check_credentials(password, username):
            return

        manager.next_screen()

        main_check = True

    def _reset(self):
        self.ids["addr_box"].ids["box_val"].text = "localhost"
        self.ids["port_box"].ids["box_val"].text = "8090"
        self.ids["username_box"].ids["box_val"].text = self.ids["password_box"].ids["box_val"].text = ""

class MainScreen(Screen):
    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        self._keyboard.bind(on_key_down = self._on_keyboard_down)

        self.thr = threading.Thread(target = self.read_loop)
        self.thr.daemon = True
        self.thr.start()

    def read_loop(self):
        global client, main_check

        while not main_check:
            pass

        while True:
            self.ids["msg_box"].text += "\n" + client.handle_read() + "\n----------------------------------------------"

    def _keyboard_closed(self):
        print("Keyboard lost")
        # self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        self._keyboard = None 

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        global client

        if keycode[1] == 'enter': # :enter
            message = self.ids["roll_box"].text
            print(message)
            if re.match(r"^[Qq].*", message):
                self.thr.join()
                sock.close()
                App.get_running_app.stop()
                return # shouldn't be needed

            client.say_roll(self.ids["roll_box"].text)
            self.ids["roll_box"].text = ""


class Manager(ScreenManager):
    def next_screen(self):
        self.current = "main"
        Window.size = (co_window_x, co_window_y)

class main_app(App):
    in_window_x, in_window_y = in_window_x, in_window_y
    co_window_x, co_window_y = co_window_x, co_window_y

    def build(self):
        self.root = Builder.load_file('client_iface.kv')
        global manager
        manager = Manager()
        return manager

if __name__ == "__main__":
    main_app().run()