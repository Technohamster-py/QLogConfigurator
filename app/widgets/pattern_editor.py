from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
    QPlainTextEdit,
    QComboBox,
)

from app.core.parser import PatternParser
from app.dialogs.block_dialog import BlockDialog
from app.models.pattern_model import PatternModel

from app.widgets.pattern_tree import PatternTree
from app.widgets.raw_editor import RawEditor
from app.widgets.preview_widget import PreviewWidget


class PatternEditor(QWidget):

    patternChanged = Signal(str)

    def __init__(
        self,
        parent=None,
    ):
        super().__init__(parent)

        self.model = PatternModel(
            parent=self
        )

        self.parser = PatternParser()

        self.create_ui()

        self.model.modelReset.connect(
            self.refresh_output
        )

    # --------------------------------------------------------
    # UI
    # --------------------------------------------------------

    def create_ui(self):
        layout = QVBoxLayout(
            self
        )

        splitter = QSplitter(
            Qt.Horizontal
        )

        layout.addWidget(
            splitter
        )

        # ----------------------------------------------------
        # Left
        # ----------------------------------------------------

        left = QWidget()

        left_layout = QVBoxLayout(
            left
        )

        left_layout.addWidget(
            QLabel(
                "Pattern blocks"
            )
        )

        self.tree = PatternTree()

        self.tree.setModel(
            self.model
        )

        self.tree.setColumnWidth(
            0,
            140,
        )

        self.tree.blockDoubleClicked.connect(
            self.edit_block
        )

        left_layout.addWidget(
            self.tree
        )

        buttons = QHBoxLayout()

        add_button = QPushButton(
            "Add"
        )

        add_button.clicked.connect(
            self.add_block
        )

        buttons.addWidget(
            add_button
        )

        edit_button = QPushButton(
            "Edit"
        )

        edit_button.clicked.connect(
            self.edit_current
        )

        buttons.addWidget(
            edit_button
        )

        remove_button = QPushButton(
            "Remove"
        )

        remove_button.clicked.connect(
            self.remove_current
        )

        buttons.addWidget(
            remove_button
        )

        left_layout.addLayout(
            buttons
        )

        move_buttons = QHBoxLayout()

        up_button = QPushButton(
            "Move up"
        )

        up_button.clicked.connect(
            self.move_up
        )

        move_buttons.addWidget(
            up_button
        )

        down_button = QPushButton(
            "Move down"
        )

        down_button.clicked.connect(
            self.move_down
        )

        move_buttons.addWidget(
            down_button
        )

        left_layout.addLayout(
            move_buttons
        )

        splitter.addWidget(
            left
        )

        # ----------------------------------------------------
        # Right
        # ----------------------------------------------------

        right = QWidget()

        right_layout = QVBoxLayout(
            right
        )

        self.mode_combo = QComboBox()

        self.mode_combo.addItems(
            [
                "Visual",
                "Raw",
            ]
        )

        self.mode_combo.currentIndexChanged.connect(
            self.mode_changed
        )

        right_layout.addWidget(
            self.mode_combo
        )

        self.generated = QPlainTextEdit()

        self.generated.setReadOnly(
            True
        )

        self.generated.setMaximumHeight(
            100
        )

        right_layout.addWidget(
            QLabel(
                "Generated pattern"
            )
        )

        right_layout.addWidget(
            self.generated
        )

        self.raw_editor = RawEditor()

        self.raw_editor.setVisible(
            False
        )

        self.raw_editor.patternEdited.connect(
            self.raw_pattern_changed
        )

        right_layout.addWidget(
            self.raw_editor
        )

        right_layout.addWidget(
            QLabel(
                "Preview"
            )
        )

        self.preview = PreviewWidget()

        right_layout.addWidget(
            self.preview
        )

        splitter.addWidget(
            right
        )

        splitter.setStretchFactor(
            0,
            1,
        )

        splitter.setStretchFactor(
            1,
            2,
        )

    # --------------------------------------------------------
    # Selection
    # --------------------------------------------------------

    def current_index(self):
        return self.tree.currentIndex()

    def current_block(self):
        return self.model.block_from_index(
            self.current_index()
        )

    # --------------------------------------------------------
    # Add
    # --------------------------------------------------------

    def add_block(self):
        current = self.current_block()

        dialog = BlockDialog(
            self
        )

        if dialog.exec() != dialog.Accepted:
            return

        block = dialog.block()

        if (
            current is not None
            and current.is_container()
        ):
            self.model.add_block(
                block,
                parent=current,
            )

            self.tree.expand(
                self.current_index()
            )

        else:
            parent = (
                self.model.find_parent(
                    current
                )
                if current
                else None
            )

            siblings = (
                self.model.blocks()
                if parent is None
                else parent.children
            )

            row = (
                siblings.index(current) + 1
                if current in siblings
                else len(siblings)
            )

            self.model.add_block(
                block,
                parent,
                row,
            )

        self.refresh_output()

    # --------------------------------------------------------
    # Edit
    # --------------------------------------------------------

    def edit_current(self):
        index = self.current_index()

        if not index.isValid():
            return

        self.edit_block(index)

    def edit_block(self, index):
        block = self.model.block_from_index(
            index
        )

        if block is None:
            return

        dialog = BlockDialog(
            self,
            block,
        )

        if dialog.exec() != dialog.Accepted:
            return

        replacement = dialog.block()

        replacement.children = (
            block.children
        )

        parent = self.model.find_parent(
            block
        )

        siblings = (
            self.model.blocks()
            if parent is None
            else parent.children
        )

        row = siblings.index(
            block
        )

        siblings[row] = replacement

        self.model.dataChanged.emit(
            self.model.index_for_block(
                replacement
            ),
            self.model.index_for_block(
                replacement
            ),
        )

        self.refresh_output()

    # --------------------------------------------------------
    # Remove
    # --------------------------------------------------------

    def remove_current(self):
        block = self.current_block()

        if block is None:
            return

        self.model.remove_block(
            block
        )

        self.refresh_output()

    # --------------------------------------------------------
    # Move
    # --------------------------------------------------------

    def move_up(self):
        block = self.current_block()

        if block is None:
            return

        siblings = self.model.siblings_for(
            block
        )

        row = siblings.index(
            block
        )

        if row > 0:
            self.model.move_block(
                block,
                row - 1,
            )

            self.refresh_output()

    def move_down(self):
        block = self.current_block()

        if block is None:
            return

        siblings = self.model.siblings_for(
            block
        )

        row = siblings.index(
            block
        )

        if row < len(siblings) - 1:
            self.model.move_block(
                block,
                row + 1,
            )

            self.refresh_output()

    # --------------------------------------------------------
    # Pattern
    # --------------------------------------------------------

    def pattern(self) -> str:
        return self.model.pattern()

    def set_pattern(
        self,
        pattern: str,
    ):
        blocks = self.parser.parse(
            pattern
        )

        self.model.set_blocks(
            blocks
        )

        self.refresh_output()

    def refresh_output(self):
        pattern = self.pattern()

        self.generated.setPlainText(
            pattern
        )

        self.raw_editor.set_pattern(
            pattern
        )

        self.preview.set_blocks(
            self.model.blocks()
        )

        self.patternChanged.emit(
            pattern
        )

    # --------------------------------------------------------
    # Raw
    # --------------------------------------------------------

    def raw_pattern_changed(
        self,
        pattern: str,
    ):
        try:
            blocks = self.parser.parse(
                pattern
            )

        except ValueError:
            return

        self.model.set_blocks(
            blocks
        )

        self.generated.setPlainText(
            pattern
        )

        self.preview.set_blocks(
            blocks
        )

        self.patternChanged.emit(
            pattern
        )

    # --------------------------------------------------------
    # Mode
    # --------------------------------------------------------

    def mode_changed(
        self,
        index: int,
    ):
        self.raw_editor.setVisible(
            index == 1
        )

        self.generated.setVisible(
            True
        )