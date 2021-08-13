#include <QCoreApplication>
#include <maincontroller.h>
#include <QTimer>

int main(int argc, char *argv[])
{
    QCoreApplication app(argc, argv);
    MainController main_controller(app, nullptr);
    QTimer::singleShot(0, &main_controller, &MainController::initialize);

    int mainloop_result = app.exec();

    return mainloop_result;
}
