#include "maincontroller.h"

#include <QDebug>
#include <QTimer>

MainController::MainController(QCoreApplication &app, QObject *parent) :
    QObject(parent),
    app(app)
{

}

void MainController::initialize()
{
    qDebug() << "Initializing";
    QTimer::singleShot(5000, this, &MainController::deinitialize);
}

void MainController::deinitialize()
{
    qDebug() << "Deinitializing";
    app.quit();
}
