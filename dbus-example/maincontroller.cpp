#include "maincontroller.h"

#include <QDebug>
#include <QTimer>
#include <QtDBus/QDBusConnection>
#include <QtDBus/QDBusConnectionInterface>

MainController::MainController(QCoreApplication &app, QObject *parent) :
    QObject(parent),
    app(app)
{

}

bool MainController::initialize()
{
    qDebug() << "Initializing";

    QDBusConnection bus = QDBusConnection::systemBus();
    if (!bus.isConnected())
    {
        qDebug() << "Failed to connect to the system bus.";
        return false;
    }

    QDBusConnectionInterface* dbus_conn_iface = bus.interface();
    auto reg_result = dbus_conn_iface->registerService(SERVICE_NAME,
                                                       QDBusConnectionInterface::DontQueueService,
                                                       QDBusConnectionInterface::DontAllowReplacement);
    if (reg_result.isValid())
    {
        if (reg_result.value() != 1)
        {
            qDebug() << "The bus name has already been claimed. This instance will now exit.";
            return false;
        }
    }
    else
    {
        qDebug() << reg_result.error().message();
        qDebug() << "Invalid response from D-Bus when registering a service name.";
    }

    QTimer::singleShot(10000, this, &MainController::deinitialize);
    return true;
}

void MainController::deinitialize()
{
    qDebug() << "Deinitializing";

    auto bus = QDBusConnection::systemBus();
    auto dbus_conn_iface = bus.interface();
    dbus_conn_iface->unregisterService(SERVICE_NAME);

    app.quit();
}
