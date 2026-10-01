from PySide6.QtWidgets import (
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.core.preview import (
    PreviewGenerator,
)


class PreviewWidget(QWidget):

    LEVELS = (
        "debug",
        "info",
        "warning",
        "critical",
        "fatal",
    )

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(
            self
        )

        self.editor = QPlainTextEdit()

        self.editor.setReadOnly(
            True
        )

        layout.addWidget(
            self.editor
        )

    def set_blocks(
        self,
        blocks,
    ):
        lines = []

        for level in self.LEVELS:
            result = (
                PreviewGenerator.render(
                    blocks,
                    level,
                )
            )

            lines.append(
                f"{level.upper():<9} {result}"
            )

        self.editor.setPlainText(
            "\n".join(lines)
        )