# -*- coding: utf-8 -*-
"""
AnelPowerControl
================

"""

from pprint import pprint
import logging
try:
    import requests
except ImportError:
    pass
import select
import socket 
import time
from collections import OrderedDict

logger = logging.getLogger(__name__)


class Interface(object):
    fields = (
        'name', 
        'host', 
        'ip', 
        'mask', 
        'gateway', 
        'mac', 
        'port',
        'temperature', 
        'type',
        'version',
    ) 


class HTTPInterface(Interface):
    def __init__(self, port=80):
        self.port = port

    def data(self, address, auth):
        r = requests.get('http://%s/strg.cfg' % (address, ), auth=auth)

        splitted = r.text.split(';')

        data = dict(zip(fields[:9], splitted))
        data['sockets'] = {}

        for index in range(8):
            # socket = AnelPowerControlSocket(index, name=splitted[10 + index])
            socket = {
                'index': index,
                'name': splitted[10 + index],
                'is_on': bool(int(splitted[20 + index])),
                'disabled': bool(int(splitted[30 + index])),
                'info': splitted[40 + index],
                # 'tk': _splitted[50 + i],
            }
            data['sockets'][index] = socket
            data['sockets'][socket['name']] = socket

        return data

    def switch(self, address, socket_number, state, username=None, password=None):
        r = requests.post('http://%s/ctrl.htm' % (address, ), 
                          auth=(username, password), data='F%d=T' % (socket_number, ),
                          headers={'content-type': 'text/plain'})


class UDPInterface(Interface):
    charset = 'latin'
    timeout = 1 

    def __init__(self, port_out=75, port_in=77, timeout=2):
        self.port_out = port_out
        self.port_in = port_in

        self.socket_out = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket_out.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.socket_out.settimeout(timeout)

        self.socket_in = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket_in.bind(('0.0.0.0', port_in))
        self.socket_in.settimeout(timeout)

    def _send(self, message, address='255.255.255.0', auth=None):
        self.socket_out.sendto('wer da?'.encode(self.charset), (address, self.port_out))
        rl, _, _ = select.select([self.socket_in], [], [], self.timeout)
        response, (sender, port) = self.socket_in.recvfrom(2048)

        return self.parse_response(response)
        pass

    def data(self, address, auth):
        self.socket_out.sendto('wer da?'.encode(self.charset), (address, self.port_out))
        # rl, _, _ = select.select([self.socket_in], [], [], self.timeout)
        while True:
            try:
                response, (sender, port) = self.socket_in.recvfrom(2048)
                return self.parse_response(response)
                if response:
                    break
            except socket.timeout:
                print('TIMEOUT')
        # response, (sender, port) = self.socket_in.recvfrom(2048)

        return self.parse_response(response)

    def parse_response(self, response):
        response = response.decode(self.charset)
        splitted = [v.strip() for v in response.split(':')]
        data = dict(zip(self.fields[0:5], splitted[0:5]))

        # format mac address
        data[self.fields[5]] = ':'.join('%.2X' % (int(n), ) 
                                        for n in splitted[5].split('.'))
        # format temperature
        data[self.fields[7]] = float(splitted[24].strip('°C'))
        # format version
        data[self.fields[9]] = splitted[25]

        disabled_sockets, http_port = splitted[14:16]

        power_sockets = data['power_sockets'] = OrderedDict()
        for index, socket in enumerate(splitted[6:14], 1):
            name, status = socket.split(',')

            power_socket = {
                'index': index,
                'name': name,
                'is_on': bool(int(status)),
                'disabled': bool(int(disabled_sockets) & (1 << index)),
            }
            power_sockets[name] = power_socket

        ios = data['ios'] = OrderedDict()
        for index, io in enumerate(splitted[16:24]):
            name, direction, status = io.split(',')

            ios[name] = {
                'index': index,
                'name': name,
                'is_on': bool(int(status)),
                'direction': direction,
            }

        return data

    def switch(self, address, socket_number, state, username='', password=''):
        state_str = 'on' if state else 'off'
        message = 'Sw_{}{}{}{}'.format(state_str, socket_number,  
                                       username, password)

        while True:
            self.socket_out.sendto(message.encode(self.charset), 
                                   (address, self.port_out))
            try:
                response, (sender, port) = self.socket_in.recvfrom(2048)
                print(response)
                break
            except socket.timeout:
                print('TIMEOUT-X '*3)


class PowerSocket:
    def __init__(self, control, index, name, is_on, disabled, info=None):
        self.control = control
        self.index = index
        self.name = name
        self.is_on = is_on
        self.disabled = disabled
        self.info = info

    def __repr__(self):
        status = 'on' if self.is_on else 'disabled' if self.disabled else 'off'
        return '<PowerSocket #{} - {} - {}>'.format(self.index, self.name, status)

    def on(self):
        self.control.switch(self.index, True)

    def off(self):
        self.control.switch(self.index, False)


class AnelPowerControl:
    default_interface = None

    def __init__(self, address, auth=None, interface=None):
        self.address = address
        self.auth = auth
        if interface is None:
            self.interface = AnelPowerControl.default_interface 
        else: 
            self.interface = interface

    def __getattr__(self, name):
        return self.data[name]

    def switch(self, socket_number, state):
        self.interface.switch(self.address, socket_number, state, *self.auth)

    def __getitem__(self, index):
        power_sockets = self.data['power_sockets']
        if isinstance(index, int):
            item = list(power_sockets.values())[index]
        else:
            item = power_sockets[index]
        return PowerSocket(self, **item)

    def __iter__(self):
        for power_socket in self.data['power_sockets'].values():
            yield PowerSocket(self, **power_socket)

    @property
    def data(self):
        return self.interface.data(self.address, self.auth)



if __name__ == '__main__':
    # logging.basicConfig(format='%(levelname)s:%(message)s', 
    #                     level=logging.DEBUG)
    from time import sleep
    AnelPowerControl.default_interface = UDPInterface()
    AnelPowerControl.default_interface = HTTPInterface()
    crtl = AnelPowerControl('crti-btp-sl4', auth=('admin', 'config'))
    # print(crtl.interface)
    pprint(list(crtl))
    print(crtl['BM_T01_PU2'])
    sleep(5)
    crtl['BM_T01_PU2'].on()
    # pprint(crtl.data)
    # exit()
    sleep(1)
    print(crtl['BM_T01_PU2'])
    sleep(5)
    # print(crtl['BM_T01_PU2'])
    crtl['BM_T01_PU2'].off()
    sleep(1)
    print(crtl['BM_T01_PU2'])
    sleep(5)
    sleep(5)
    print(crtl['BM_T01_PU2'])
    crtl['BM_T01_PU2'].on()
    sleep(5)
    print(crtl['BM_T01_PU2'])
    crtl['BM_T01_PU2'].off()
    sleep(5)
    print(crtl['BM_T01_PU2'])