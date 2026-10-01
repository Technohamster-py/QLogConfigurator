import sys
from PySide6.QtWidgets import QApplication
from app.windows.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)

    app.setApplicationName(
        "Qt Logging Pattern Configurator"
    )

    app.setOrganizationName(
        "Technohamster"
    )

    window = MainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())