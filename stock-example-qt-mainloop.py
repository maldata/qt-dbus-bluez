#!/usr/bin/python
# SPDX-License-Identifier: LGPL-2.1-or-later

from __future__ import print_function

import sys
import argparse
import dbus
import dbus.exceptions
import dbus.service

from dbus.mainloop.pyqt5 import DBusQtMainLoop
from PyQt5.QtCore import pyqtSignal, pyqtSlot, pyqtProperty, Q_CLASSINFO, QCoreApplication, QObject, QTimer

mainloop = None

BLUEZ_SERVICE_NAME = 'org.bluez'
LE_ADVERTISING_MANAGER_IFACE = 'org.bluez.LEAdvertisingManager1'
DBUS_OM_IFACE = 'org.freedesktop.DBus.ObjectManager'
DBUS_PROP_IFACE = 'org.freedesktop.DBus.Properties'

LE_ADVERTISEMENT_IFACE = 'org.bluez.LEAdvertisement1'


class InvalidArgsException(dbus.exceptions.DBusException):
    _dbus_error_name = 'org.freedesktop.DBus.Error.InvalidArgs'


class NotSupportedException(dbus.exceptions.DBusException):
    _dbus_error_name = 'org.bluez.Error.NotSupported'


class NotPermittedException(dbus.exceptions.DBusException):
    _dbus_error_name = 'org.bluez.Error.NotPermitted'


class InvalidValueLengthException(dbus.exceptions.DBusException):
    _dbus_error_name = 'org.bluez.Error.InvalidValueLength'


class FailedException(dbus.exceptions.DBusException):
    _dbus_error_name = 'org.bluez.Error.Failed'


class Advertisement(dbus.service.Object):
    PATH_BASE = '/org/bluez/example/advertisement'

    def __init__(self, bus, index, advertising_type):
        self.path = self.PATH_BASE + str(index)
        self.bus = bus
        self.ad_type = advertising_type
        self.service_uuids = None
        self.manufacturer_data = None
        self.solicit_uuids = None
        self.service_data = None
        self.local_name = None
        self.include_tx_power = False
        self.data = None
        dbus.service.Object.__init__(self, bus, self.path)

    def get_properties(self):
        properties = dict()
        properties['Type'] = self.ad_type
        if self.service_uuids is not None:
            properties['ServiceUUIDs'] = dbus.Array(self.service_uuids,
                                                    signature='s')
        if self.solicit_uuids is not None:
            properties['SolicitUUIDs'] = dbus.Array(self.solicit_uuids,
                                                    signature='s')
        if self.manufacturer_data is not None:
            properties['ManufacturerData'] = dbus.Dictionary(
                self.manufacturer_data, signature='qv')
        if self.service_data is not None:
            properties['ServiceData'] = dbus.Dictionary(self.service_data,
                                                        signature='sv')
        if self.local_name is not None:
            properties['LocalName'] = dbus.String(self.local_name)
        if self.include_tx_power:
            properties['Includes'] = dbus.Array(["tx-power"], signature='s')

        if self.data is not None:
            properties['Data'] = dbus.Dictionary(
                self.data, signature='yv')
        return {LE_ADVERTISEMENT_IFACE: properties}

    def get_path(self):
        return dbus.ObjectPath(self.path)

    def add_service_uuid(self, uuid):
        if not self.service_uuids:
            self.service_uuids = []
        self.service_uuids.append(uuid)

    def add_solicit_uuid(self, uuid):
        if not self.solicit_uuids:
            self.solicit_uuids = []
        self.solicit_uuids.append(uuid)

    def add_manufacturer_data(self, manuf_code, data):
        if not self.manufacturer_data:
            self.manufacturer_data = dbus.Dictionary({}, signature='qv')
        self.manufacturer_data[manuf_code] = dbus.Array(data, signature='y')

    def add_service_data(self, uuid, data):
        if not self.service_data:
            self.service_data = dbus.Dictionary({}, signature='sv')
        self.service_data[uuid] = dbus.Array(data, signature='y')

    def add_local_name(self, name):
        if not self.local_name:
            self.local_name = ""
        self.local_name = dbus.String(name)

    def add_data(self, ad_type, data):
        if not self.data:
            self.data = dbus.Dictionary({}, signature='yv')
        self.data[ad_type] = dbus.Array(data, signature='y')

    @dbus.service.method(DBUS_PROP_IFACE,
                         in_signature='s',
                         out_signature='a{sv}')
    def GetAll(self, interface):
        print('GetAll')
        if interface != LE_ADVERTISEMENT_IFACE:
            raise InvalidArgsException()
        print('returning props')
        return self.get_properties()[LE_ADVERTISEMENT_IFACE]

    @dbus.service.method(LE_ADVERTISEMENT_IFACE,
                         in_signature='',
                         out_signature='')
    def Release(self):
        print('%s: Released!' % self.path)


class TestAdvertisement(Advertisement):
    def __init__(self, bus, index):
        Advertisement.__init__(self, bus, index, 'peripheral')
        self.add_service_uuid('180D')
        self.add_service_uuid('180F')
        self.add_manufacturer_data(0xffff, [0x00, 0x01, 0x02, 0x03])
        #self.add_service_data('9999', [0x00, 0x01, 0x02, 0x03, 0x04])
        self.add_local_name('TestAdvertisement')
        self.include_tx_power = True
        #self.add_data(0x26, [0x01, 0x01, 0x00])


class MainController(QObject):
    def __init__(self, app, parent=None):
        super().__init__(parent)

        self._app = app
        self._bus = None
        self._adapter_props = None
        self._ad_manager = None
        self._test_advertisement = None

    def startup(self):
        print('Starting main controller')
        self._bus = dbus.SystemBus()
        self._bus.request_name("com.github.maldata.testservice1")

        adapter = self.find_adapter()
        if not adapter:
            print('LEAdvertisingManager1 interface not found')
            return

        self._adapter_props = dbus.Interface(self._bus.get_object(BLUEZ_SERVICE_NAME, adapter),
                                             "org.freedesktop.DBus.Properties")

        self._adapter_props.Set("org.bluez.Adapter1", "Powered", dbus.Boolean(1))

        self._ad_manager = dbus.Interface(self._bus.get_object(BLUEZ_SERVICE_NAME, adapter),
                                          LE_ADVERTISING_MANAGER_IFACE)

        self._test_advertisement = TestAdvertisement(self._bus, 0)

        self._ad_manager.RegisterAdvertisement(self._test_advertisement.get_path(), {},
                                               reply_handler=self.ad_registration_ok,
                                               error_handler=self.ad_registration_failed)

    def shutdown(self):
        self._ad_manager.UnregisterAdvertisement(self._test_advertisement)
        print('Advertisement unregistered')
        dbus.service.Object.remove_from_connection(self._test_advertisement)
        self._app.quit()

    def find_adapter(self):
        remote_om = dbus.Interface(self._bus.get_object(BLUEZ_SERVICE_NAME, '/'),
                                   DBUS_OM_IFACE)
        objects = remote_om.GetManagedObjects()

        for o, props in objects.items():
            if LE_ADVERTISING_MANAGER_IFACE in props:
                return o

        return None

    def ad_registration_ok(self):
        print('Registered OK')

    def ad_registration_failed(self):
        print('Registration failed')


def main(timeout=0):
    global mainloop

    # If we were able to claim our dbus name, then we can go ahead.
    app = QCoreApplication(sys.argv)
    main_controller = MainController(app)
    QTimer.singleShot(0, main_controller.startup)

    DBusQtMainLoop(set_as_default=True)

    if timeout > 0:
        QTimer.singleShot(timeout * 1000, main_controller.shutdown)
    else:
        print('Advertising forever...')

    main_result = app.exec_()

    sys.exit(main_result)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--timeout', default=0, type=int, help="advertise " +
                        "for this many seconds then stop, 0=run forever " +
                        "(default: 0)")
    args = parser.parse_args()

    main(args.timeout)
