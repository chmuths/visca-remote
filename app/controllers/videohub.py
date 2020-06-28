# coding: utf-8

import time
from threading import Timer
from telnetlib import Telnet
import re
from pprint import pprint


class NotConnected(Exception):
    pass


class Videohub:

    def __init__(self, videohub_config):
        self._host = videohub_config["ip"]
        self._port = videohub_config["port"]
        self.connection = None
        self.connected = False
        self._timer = None
        self.is_running = False
        self.videohub = {'VIDEOHUB DEVICE': {},
                         'INPUT LABELS': {},
                         'OUTPUT LABELS': {},
                         'ROUTING': {}}

    def get_connection(self):
        if self.connection:
            return self.connection
        else:
            try:
                self.connection = Telnet(self._host, self._port)
                self.connected = True
                self.__start()
                return self.connection
            except OSError as ex:
                print(f"Got OSError: {ex}")
                self.connection = None
                self.connected = False
                raise NotConnected

    def __start(self):
        if not self.is_running:
            self._timer = Timer(0.1, self.__vh_read_stream)
            self._timer.start()
            self.is_running = True

    def __stop(self):
        if self.is_running:
            self._timer.cancel()
            self.is_running = False

    def __vh_read_block(self):
        try:
            response = self.get_connection().read_until(b"\n\n", timeout=.01).decode('utf-8')
            return response
        except NotConnected:
            self.connection = None
            self.connected = False
            return None

    def __vh_read_stream(self):
        """
        Timer callback method
        Reads whatever comes from VideoHub and updates strcture accordingly
        :return: None
        """
        response = self.__vh_read_block()
        if response:
            self.__vh_receive_data(response)
        self.__stop()
        self.__start()

    def __vh_receive_data(self, response):
        """
        Parse the block of data received and update videohub dict accordingly
        :param response: String with multiple lines to parse
        :return: None
        """

        response_lines = response.split("\n")
        if 'VIDEOHUB DEVICE' in response_lines[0]:
            device_dict = {}
            for response_line in response_lines[1:]:
                if ':' in response_line:
                    key, value = response_line.split(":")
                    device_dict[key] = value
            self.videohub['VIDEOHUB DEVICE'].update(device_dict)
        elif 'INPUT LABELS' in response_lines[0]:
            inputs_dict = {}
            for response_line in response_lines[1:]:
                elements = re.search('([0-9]*) (.*)', response_line)
                if elements:
                    inputs_dict[int(elements.group(1))] = elements.group(2)
            self.videohub['INPUT LABELS'].update(inputs_dict)
        elif 'OUTPUT LABELS' in response_lines[0]:
            outputs_dict = {}
            for response_line in response_lines[1:]:
                elements = re.search('([0-9]*) (.*)', response_line)
                if elements:
                    outputs_dict[int(elements.group(1))] = elements.group(2)
            self.videohub['OUTPUT LABELS'].update(outputs_dict)
        elif 'VIDEO OUTPUT ROUTING' in response_lines[0]:
            routing_dict = {}
            for response_line in response_lines[1:]:
                elements = re.search('([0-9]*) (.*)', response_line)
                if elements:
                    routing_dict[int(elements.group(1))] = int(elements.group(2))
            self.videohub['ROUTING'].update(routing_dict)
        elif 'ACK' in response_lines[0]:
            print("Received ACK")
        elif 'NAK' in response_lines[0]:
            print("Received NAK")
        else:
            pass

    def vh_request(self, data):
        """
        Send data to the VideoHub and return the response. When reading the response, a message triggered by another
        action may be returned because the protocol is async
        :param data: Body of the call
        :return: Http Response of the call
        """
        self.__stop()
        try:
            self.get_connection().write(data.encode('ascii') + b"\n\n")
        except NotConnected:
            self.connection = None
            self.connected = False
            return None

        self.__start()

    def connect(self, vh_output: int, vh_input: int):
        """
        connect output to given input
        :param vh_output: To output to change
        :param vh_input: The input to assign tou output
        :return: None
        """
        cmd_string = f"VIDEO OUTPUT ROUTING:\n{vh_output} {vh_input}"
        self.vh_request(cmd_string)


if __name__ == '__main__':
    config = {
        "ip": "192.168.0.242",
        "port": "9990",
        "output": 8,
        "inputs": [
            {
                "pgm": 12,
                "pvw": 13,
                "aux": 14
            }
        ]
    }
    videohub = Videohub(config)

    time.sleep(1)
    pprint(videohub.videohub)
    print("*******************************")
    videohub.connect(1, 5)
    time.sleep(2)
    pprint(videohub.videohub['INPUT LABELS'])
    print("*******************************")
    videohub.connect(1, 4)
    time.sleep(2)
    pprint(videohub.videohub)
    print("*******************************")
