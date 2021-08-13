#ifndef MAINCONTROLLER_H
#define MAINCONTROLLER_H

#include <QObject>
#include <QCoreApplication>

#define SERVICE_NAME "com.github.maldata.testservice1"

class MainController : public QObject
{
    Q_OBJECT
public:
    explicit MainController(QCoreApplication &app, QObject *parent = nullptr);

    bool initialize();
    void deinitialize();

signals:

private:
    QCoreApplication &app;
};

#endif // MAINCONTROLLER_H
