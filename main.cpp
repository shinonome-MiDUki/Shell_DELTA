#include <QApplication>
#include <QWidget>
#include <QLabel>

int main(int argc, char *argv[]) {
    QApplication app(argc, argv);

    QWidget window;
    window.setWindowTitle("First Qt App");
    window.resize(350, 150);

    QLabel label("Hello, Qt from Terminal!", &window);
    label.move(80, 60);

    window.show();
    return app.exec();
}
