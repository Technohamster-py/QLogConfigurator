from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QToolBar,
)

from app.core.parser import PatternParser
from app.core.serializer import PatternSerializer
from app.widgets.pattern_editor import PatternEditor


DEFAULT_PATTERN = (
    "[%{time yyyy.MM.dd h:mm:ss.zzz ttt} "
    "%{if-debug}D%{endif}"
    "%{if-info}I%{endif}"
    "%{if-warning}W%{endif}"
    "%{if-critical}C%{endif}"
    "%{if-fatal}F%{endif}]:: "
    "%{if-category}%{category}: %{endif}"
    "%{if-critical}|IN %{function}| %{endif}"
    "%{if-fatal}|IN %{function}| %{endif}"
    "%{message}"
)


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle(
            "Qt Logging Pattern Configurator"
        )

        self.resize(
            1250,
            800,
        )

        self.editor = PatternEditor()

        self.setCentralWidget(
            self.editor
        )

        self.create_actions()
        self.create_toolbar()

        self.editor.set_pattern(
            DEFAULT_PATTERN
        )

    # --------------------------------------------------------
    # Actions
    # --------------------------------------------------------

    def create_actions(self):
        self.new_action = QAction(
            "New",
            self,
        )

        self.new_action.triggered.connect(
            self.new_pattern
        )

        self.open_action = QAction(
            "Open...",
            self,
        )

        self.open_action.triggered.connect(
            self.open_pattern
        )

        self.save_action = QAction(
            "Save...",
            self,
        )

        self.save_action.triggered.connect(
            self.save_pattern
        )

        self.copy_action = QAction(
            "Copy",
            self,
        )

        self.copy_action.triggered.connect(
            self.copy_pattern
        )

        self.apply_action = QAction(
            "Apply",
            self,
        )

        self.apply_action.triggered.connect(
            self.apply_pattern
        )

    # --------------------------------------------------------
    # Toolbar
    # --------------------------------------------------------

    def create_toolbar(self):
        toolbar = QToolBar(
            "Main"
        )

        toolbar.setMovable(
            False
        )

        toolbar.addAction(
            self.new_action
        )

        toolbar.addAction(
            self.open_action
        )

        toolbar.addAction(
            self.save_action
        )

        toolbar.addSeparator()

        toolbar.addAction(
            self.copy_action
        )

        toolbar.addAction(
            self.apply_action
        )

        self.addToolBar(
            toolbar
        )

    # --------------------------------------------------------
    # New
    # --------------------------------------------------------

    def new_pattern(self):
        self.editor.model.set_blocks(
            []
        )

        self.editor.refresh_output()

    # --------------------------------------------------------
    # Open
    # --------------------------------------------------------

    def open_pattern(self):
        filename, _ = (
            QFileDialog.getOpenFileName(
                self,
                "Open pattern",
                "",
                "Logging pattern (*.json)",
            )
        )

        if not filename:
            return

        try:
            blocks = PatternSerializer.load(
                filename
            )

            self.editor.model.set_blocks(
                blocks
            )

            self.editor.refresh_output()

        except (
            OSError,
            ValueError,
            KeyError,
            TypeError,
        ) as error:
            QMessageBox.critical(
                self,
                "Open error",
                str(error),
            )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    def save_pattern(self):
        filename, _ = (
            QFileDialog.getSaveFileName(
                self,
                "Save pattern",
                "",
                "Logging pattern (*.json)",
            )
        )

        if not filename:
            return

        try:
            PatternSerializer.save(
                filename,
                self.editor.model.blocks(),
            )

        except OSError as error:
            QMessageBox.critical(
                self,
                "Save error",
                str(error),
            )

    # --------------------------------------------------------
    # Copy
    # --------------------------------------------------------

    def copy_pattern(self):
        self.editor.window().windowHandle()

        self.editor.setFocus()

        self.editor.generated.selectAll()

        self.editor.generated.copy()

        self.editor.generated.moveCursor(
            self.editor.generated.textCursor().Start
        )

        self.statusBar().showMessage(
            "Pattern copied",
            3000,
        )

    # --------------------------------------------------------
    # Apply
    # --------------------------------------------------------

    def apply_pattern(self):
        pattern = self.editor.pattern()

        from PySide6.QtWidgets import QApplication

        QApplication.clipboard().setText(
            pattern
        )

        QMessageBox.information(
            self,
            "Pattern",
            "Generated pattern copied to clipboard.\n\n"
            "Use it in your Qt application with:\n\n"
            "qSetMessagePattern(pattern);",
        )