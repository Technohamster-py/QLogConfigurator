from PySide6.QtCore import Signal
from PySide6.QtWidgets import QPlainTextEdit


class RawEditor(QPlainTextEdit):

    patternEdited = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.textChanged.connect(
            self._text_changed
        )

        self._updating = False

    def set_pattern(
        self,
        pattern: str,
    ):
        self._updating = True

        self.setPlainText(
            pattern
        )

        self._updating = False

    def _text_changed(self):
        if self._updating:
            return

        self.patternEdited.emit(
            self.toPlainText()
        )