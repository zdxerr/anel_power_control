# -*- coding: utf-8 -*-
"""
AnelPowerControl
================

"""

from pprint import pprint
import logging
import requests

# logging.basicConfig(format='%(levelname)s:%(message)s', 
#                     level=logging.DEBUG)
logger = logging.getLogger(__name__)


class AnelPowerControl:
    def __init__(self, address, auth=None):
        self.address = address
        self.auth = auth

    def __getattr__(self, name):
        return self.data[name]

    class Socket:
        def __init__(self, control, index, name, is_on, disabled, info):
            self.control = control
            self.index = index
            self.name = name
            self.is_on = is_on
            self.disabled = disabled
            self.info = info

        def __repr__(self):
            return '<AnelPowerControl.Socket #%d - %s - %s>' % (
                self.index, self.name, 
                'on' if self.is_on else 'disabled' if self.disabled else 'off')

        def on(self):
            if not self.is_on:
                logger.info('%s #%d (%s) turning on', self.control.address, 
                            self.index, self.name)
                self.control.control('F%d=T' % (self.index, ))
            else:
                logger.debug('%s #%d (%s) already on', self.control.address, 
                             self.index, self.name)

        def off(self):
            if self.is_on:
                logger.info('%s #%d (%s) turning off', self.control.address, 
                            self.index, self.name)
                self.control.control('F%d=T' % (self.index, ))
            else:
                logger.debug('%s #%d (%s) already off', self.control.address, 
                             self.index, self.name)


    def __getitem__(self, index):
        return self.Socket(self, **self.data['sockets'][index])

    def __iter__(self):
        for index in range(8):
            yield self.Socket(self, **self.data['sockets'][index])

    @property
    def data(self):
        r = requests.get('http://%s/strg.cfg' % (self.address, ), 
                         auth=self.auth)

        fields = (
            'name', 'host', 'ip', 'mask', 'gateway', 'mac', 'port',
            'temperature', 'type'
        ) 
        splitted = r.text.split(';')

        data = dict(zip(fields, splitted))
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

    def control(self, data):
        r = requests.post('http://%s/ctrl.htm' % (self.address, ), 
                          auth=self.auth, data=data,
                          headers={'content-type': 'text/plain'})


if __name__ == '__main__':
    
    from time import sleep
    crtl = AnelPowerControl('crti-btp-sl3', auth=('admin', 'config'))
    pprint(crtl.data)
    print(crtl[1])
    sleep(0.5)
    crtl['PowerSupply 12V'].on()
    # pprint(crtl.data)
    sleep(0.5)
    print(crtl['PowerSupply 12V'])
    crtl['PowerSupply 12V'].off()
    sleep(0.5)
    print(crtl['PowerSupply 12V'])
    crtl['PowerSupply 12V'].on()
    sleep(0.5)
    print(crtl['PowerSupply 12V'])
    crtl['PowerSupply 12V'].off()
    sleep(0.5)
    print(crtl['PowerSupply 12V'])
