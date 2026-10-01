from PySide6.QtWidgets import QTreeView
from PySide6.QtCore import Signal


class PatternTree(QTreeView):

    blockDoubleClicked = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setAlternatingRowColors(
            True
        )

        self.setUniformRowHeights(
            True
        )

        self.setSelectionBehavior(
            QTreeView.SelectRows
        )

        self.setEditTriggers(
            QTreeView.NoEditTriggers
        )

        self.doubleClicked.connect(
            self.on_double_click
        )

    def on_double_click(self, index):
        self.blockDoubleClicked.emit(
            index
        )