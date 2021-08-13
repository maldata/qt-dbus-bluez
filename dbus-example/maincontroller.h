#ifndef MAINCONTROLLER_H
#define MAINCONTROLLER_H

#include <QObject>
#include <QCoreApplication>

class MainController : public QObject
{
    Q_OBJECT
public:
    explicit MainController(QCoreApplication &app, QObject *parent = nullptr);

    void initialize();
    void deinitialize();

signals:

private:
    QCoreApplication &app;
};

#endif // MAINCONTROLLER_H
