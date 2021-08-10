import sys

from PyQt5.QtCore import pyqtSignal, pyqtSlot, pyqtProperty, Q_CLASSINFO, QCoreApplication, QObject, QTimer
from PyQt5.QtDBus import QDBus, QDBusAbstractInterface, QDBusReply, QDBusConnection, QDBusMessage, QDBusAbstractAdaptor, QDBusConnectionInterface, QDBusObjectPath, QDBusVariant


class ExampleObject(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._adapter = ExampleAdapter(self)
        self._adapter2 = AnotherAdapter(self)
        self._type = 'peripheral'

    @property
    def type(self):
        return self._type
    

class ExampleAdapter(QDBusAbstractAdaptor):
    Q_CLASSINFO("D-Bus Interface", "com.github.maldata.sampleiface1")
#    Q_CLASSINFO('D-Bus Introspection', ''
#                '  <interface name="com.github.maldata.sampleiface1">\n'
#                '    <method name="DoThing" />\n'
#                '    <property access="read" type="s" name="SampleStringProp" />'
#                '    <property access="read" type="as" name="SampleStringListProp" />'
#                '    <property access="read" type="a{sv}" name="SampleStrStrDictProp" />'
#                '    <property access="read" type="a{sv}" name="SampleStrIntDictProp" />'
#                '  </interface>\n'
#                '')
#
#"    <method name=\"addUser\">\n"
#"      <arg direction=\"in\" type=\"s\" name=\"user\"/>\n"
#"    </method>\n"

    def __init__(self, parent):
        super().__init__(parent)
        self.setAutoRelaySignals(True)

    @pyqtProperty(str)
    def SampleStringProp(self):
        return "whatever"

    @pyqtProperty('QStringList')
    def SampleStringListProp(self):
        return ["thing1", "thing2"]

    # We use QVariantMap for dictionaries with string keys
    @pyqtProperty('QVariantMap')
    def SampleStrStrDictProp(self):
        return {'key1': 'value1', 'key2': 'value2'}

    # We use QVariantMap for dictionaries with string keys
    @pyqtProperty('QVariantMap')
    def SampleStrIntDictProp(self):
        return {'key': 4}

    @pyqtProperty('QVariantMap')
    def SampleStdDict(self):
        return {'keyA': 'smorg'}
        
    @pyqtSlot()
    def DoThing(self):
        pass


class AnotherAdapter(QDBusAbstractAdaptor):
    Q_CLASSINFO("D-Bus Interface", "org.bluez.LEAdvertisement1")
#    Q_CLASSINFO('D-Bus Introspection', ''
#                '  <interface name="org.bluez.LEAdvertisement1">'
#                '    <method name="Release" />'
#                '    <property access="read" type="s" name="Type" />'
#                '    <property access="read" type="s" name="LocalName" />'
#                '    <property access="read" type="as" name="Includes" />'
#                '    <property access="read" type="as" name="ServiceUUIDs" />'
#                '  </interface>'
#                '')
#                '    <property access="read" type="a{sv}" name="ServiceData" />'
    
    def __init__(self, parent):
        super().__init__(parent)
        self.setAutoRelaySignals(True)

    @pyqtSlot()
    def Release(self):
        print('Releasing.')

    @pyqtProperty(str)
    def Type(self):
        return self.parent().type
    
    @pyqtProperty(str)
    def LocalName(self):
        return 'I am advertising!'

    # Looks like we need to specify a QStringList (by string name, not by type...
    # the type doesn't exist in pyqt!)
    @pyqtProperty('QStringList')
    def Includes(self):
        return ['tx-power']

    @pyqtProperty('QStringList')
    def ServiceUUIDs(self):
        return ['180D', '180F']

#    @pyqtProperty('QVariantMap')
#    def ServiceData(self):
#        return {'9999': [0x00, 0x01, 0x02, 0x03, 0x04]}
#    
#    @pyqtProperty('QVariantMap')
#    def ManufacturerData(self):
#        return {0xffff: [0x00, 0x01, 0x02, 0x03]}


class BleAdManager(QDBusAbstractInterface):
    def __init__(self, dbus_obj_path, parent=None):
        self._ble_adapter_dbus_path = dbus_obj_path
        self._dbus_system_bus = QDBusConnection.systemBus()

        super().__init__("org.bluez",
                         self._ble_adapter_dbus_path,
                         "org.bluez.LEAdvertisingManager1",
                         self._dbus_system_bus,
                         parent)

    def RegisterAdvertisement(self, ad_path):
        print("Registering {0}...".format(ad_path))
        msg = self.call(QDBus.CallMode.NoBlock,
                        'RegisterAdvertisement',
                        QDBusObjectPath(ad_path),
                        {})
        print("Call returned.")
        reply = QDBusReply(msg)

        if reply.isValid():
            print("Valid")
            return reply.value()
        else:
            print(reply.error().message())
            return None

        

class MainController(QObject):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app = app
        self._test_obj = ExampleObject()
        
    def startup(self):
        print("Startup")
        QTimer.singleShot(60000, self.shutdown)

        bus = QDBusConnection.systemBus()
        obj_name="/com/github/maldata/TestObj1"
        result = bus.registerObject(obj_name, self._test_obj)

        ad_mgr = BleAdManager("/org/bluez/hci0")
        ad_mgr.RegisterAdvertisement(obj_name)
        
    def shutdown(self):
        print("Shutdown")
        self._app.quit()

def main():
    # Ensure that the D-Bus bus is available.
    bus = QDBusConnection.systemBus()
    if not bus.isConnected():
        sys.exit("Cannot connect to the D-Bus bus.")

    # Claim a dbus name. If it's taken, this is already running. Don't run another instance.
    dbus_conn_iface = bus.interface()
    service_name="com.github.maldata.testservice1"
    r = dbus_conn_iface.registerService(service_name,
                                        QDBusConnectionInterface.DontQueueService,
                                        QDBusConnectionInterface.DontAllowReplacement)

    if r.isValid():
        if r.value() != 1:
            msg = """The bus name {0} has already been claimed, so it seems like
    there's already an instance of the updater running. This instance will now exit."""
            msg = msg.format(service_name)
            sys.exit(msg)
    else:
        print(r.error().message())
        sys.exit("Invalid response from D-Bus when registering a service name.")

    # If we were able to claim our dbus name, then we can go ahead.
    app = QCoreApplication(sys.argv)
    main_controller = MainController(app)
    QTimer.singleShot(0, main_controller.startup)

    main_result = app.exec_()

    r = dbus_conn_iface.unregisterService(service_name)
    
    sys.exit(main_result)


if __name__ == '__main__':
    main()
