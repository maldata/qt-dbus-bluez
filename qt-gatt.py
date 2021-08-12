import sys

from PyQt5.QtCore import pyqtSignal, pyqtSlot, pyqtProperty, Q_CLASSINFO, QCoreApplication, QObject, QTimer, QMetaType, QVariant
from PyQt5.QtDBus import QDBus, QDBusAbstractInterface, QDBusReply, QDBusConnection, QDBusMessage, QDBusAbstractAdaptor, QDBusConnectionInterface, QDBusObjectPath, QDBusVariant, QDBusArgument


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

    @pyqtProperty('QByteArray')
    def SampleByteArray(self):
        return b'\x0f\x0e\x0d\x0c\x0b'
    
    @pyqtSlot()
    def DoThing(self):
        pass


class AnotherAdapter(QDBusAbstractAdaptor):
    Q_CLASSINFO("D-Bus Interface", "org.freedesktop.DBus.ObjectManager")
    Q_CLASSINFO('D-Bus Introspection', ''
                                       '  <interface name="org.freedesktop.DBus.ObjectManager">'
                                       '    <method name="GetManagedObjects">'
                                       '      <arg direction="out" type="a{oa{sa{sv}}}" name="objs" />'
                                       '    </method>'
                                       '  </interface>\n'
                                       '')
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAutoRelaySignals(True)

    @pyqtSlot(QDBusMessage)
    def GetManagedObjects(self, msg_in):
        print("GLARRRRRRRRG")
        print(msg_in)
        print(msg_in.arguments())
        print(msg_in.service())
        print(msg_in.path())
        print(msg_in.interface())
        print(msg_in.member())

        arg = QDBusArgument()
        arg.beginMap(QMetaType.QString, QMetaType.QString)
        arg.beginMapEntry()
        arg.add('/com/test1')
        arg.add('test test test')

        # arg.beginMap(QMetaType.QString, QMetaType.QVariantMap)
        # arg.beginMapEntry()
        # arg.add(QVariant("asdfsdg"))
        # arg.add(QVariant("adfhjedghm"))
        # arg.endMapEntry()
        # arg.endMap()

        arg.endMapEntry()
        arg.endMap()
        reply = msg_in.createReply([arg])
        bus = QDBusConnection.systemBus()
        bus.send(reply)


class MainController(QObject):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app = app
        self._test_obj = ExampleObject()
        
    def startup(self):
        print("Startup")
        QTimer.singleShot(20000, self.shutdown)

        bus = QDBusConnection.systemBus()
        obj_name = "/com/github/maldata/TestObj1"
        result = bus.registerObject(obj_name, self._test_obj)
        
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
    service_name = "com.github.maldata.testservice1"
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
