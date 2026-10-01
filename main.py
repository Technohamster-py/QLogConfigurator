import json
import re
import sys
from dataclasses import dataclass, field
from enum import Enum

from PySide6.QtCore import Qt, QAbstractItemModel, QModelIndex, Signal
from PySide6.QtGui import QAction, QFont
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QSplitter,
    QToolBar,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)


# ============================================================
# Pattern AST
# ============================================================

class BlockType(Enum):
    TEXT = "text"
    PLACEHOLDER = "placeholder"
    TIME = "time"
    CONDITIONAL = "conditional"


class Condition(Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    FATAL = "fatal"
    CATEGORY = "category"

    @property
    def title(self):
        return {
            Condition.DEBUG: "Debug",
            Condition.INFO: "Info",
            Condition.WARNING: "Warning",
            Condition.CRITICAL: "Critical",
            Condition.FATAL: "Fatal",
            Condition.CATEGORY: "Category",
        }[self]


@dataclass
class Block:
    type: BlockType

    text: str = ""
    placeholder: str = ""
    time_format: str = ""
    condition: Condition | None = None

    children: list["Block"] = field(default_factory=list)

    def to_pattern(self) -> str:
        if self.type == BlockType.TEXT:
            return self.text

        if self.type == BlockType.PLACEHOLDER:
            return f"%{{{self.placeholder}}}"

        if self.type == BlockType.TIME:
            return f"%{{time {self.time_format}}}"

        if self.type == BlockType.CONDITIONAL:
            condition = self.condition.value if self.condition else ""

            children = "".join(
                child.to_pattern()
                for child in self.children
            )

            return f"%{{if-{condition}}}{children}%{{endif}}"

        return ""

    def to_dict(self):
        return {
            "type": self.type.value,
            "text": self.text,
            "placeholder": self.placeholder,
            "time_format": self.time_format,
            "condition": (
                self.condition.value
                if self.condition
                else None
            ),
            "children": [
                child.to_dict()
                for child in self.children
            ],
        }

    @staticmethod
    def from_dict(data):
        block_type = BlockType(data["type"])

        condition = data.get("condition")

        return Block(
            type=block_type,
            text=data.get("text", ""),
            placeholder=data.get("placeholder", ""),
            time_format=data.get("time_format", ""),
            condition=(
                Condition(condition)
                if condition
                else None
            ),
            children=[
                Block.from_dict(child)
                for child in data.get("children", [])
            ],
        )


# ============================================================
# Parser
# ============================================================

class PatternParser:
    TOKEN_RE = re.compile(r"%\{([^}]*)\}")

    PLACEHOLDERS = {
        "appname",
        "category",
        "file",
        "function",
        "line",
        "message",
        "pid",
        "threadid",
        "threadname",
        "qthreadptr",
        "type",
    }

    CONDITIONS = {
        "debug": Condition.DEBUG,
        "info": Condition.INFO,
        "warning": Condition.WARNING,
        "critical": Condition.CRITICAL,
        "fatal": Condition.FATAL,
        "category": Condition.CATEGORY,
    }

    @classmethod
    def parse(cls, pattern: str) -> list[Block]:
        root = []
        stack = [root]

        position = 0

        for match in cls.TOKEN_RE.finditer(pattern):
            if match.start() > position:
                stack[-1].append(
                    Block(
                        type=BlockType.TEXT,
                        text=pattern[position:match.start()],
                    )
                )

            token = match.group(1)

            if token.startswith("if-"):
                condition_name = token[3:]

                if condition_name not in cls.CONDITIONS:
                    raise ValueError(
                        f"Unknown condition: {condition_name}"
                    )

                block = Block(
                    type=BlockType.CONDITIONAL,
                    condition=cls.CONDITIONS[condition_name],
                )

                stack[-1].append(block)

                stack.append(block.children)

            elif token == "endif":
                if len(stack) == 1:
                    raise ValueError(
                        "Unexpected %{endif}"
                    )

                stack.pop()

            elif token.startswith("time"):
                time_format = token[4:].strip()

                if not time_format:
                    raise ValueError(
                        "%{time} requires a format"
                    )

                stack[-1].append(
                    Block(
                        type=BlockType.TIME,
                        time_format=time_format,
                    )
                )

            elif token in cls.PLACEHOLDERS:
                stack[-1].append(
                    Block(
                        type=BlockType.PLACEHOLDER,
                        placeholder=token,
                    )
                )

            else:
                raise ValueError(
                    f"Unknown Qt logging token: %{{{token}}}"
                )

            position = match.end()

        if position < len(pattern):
            stack[-1].append(
                Block(
                    type=BlockType.TEXT,
                    text=pattern[position:],
                )
            )

        if len(stack) != 1:
            raise ValueError(
                "Unclosed conditional block"
            )

        return root


# ============================================================
# Preview
# ============================================================

class PreviewGenerator:
    SAMPLE_VALUES = {
        "appname": "LoggingConfigurator",
        "category": "my.category",
        "file": "main.cpp",
        "function": "MyClass::doSomething()",
        "line": "123",
        "message": "Something happened",
        "pid": "12345",
        "threadid": "0x123456",
        "threadname": "MainThread",
        "qthreadptr": "0x7ffdeadbeef",
    }

    @classmethod
    def render(
        cls,
        blocks: list[Block],
        level: str,
    ) -> str:
        result = []

        for block in blocks:
            if block.type == BlockType.TEXT:
                result.append(block.text)

            elif block.type == BlockType.PLACEHOLDER:
                if block.placeholder == "type":
                    result.append(level.upper())
                else:
                    result.append(
                        cls.SAMPLE_VALUES.get(
                            block.placeholder,
                            f"<{block.placeholder}>",
                        )
                    )

            elif block.type == BlockType.TIME:
                result.append("2026.09.28 10:51:23.421 MSK")

            elif block.type == BlockType.CONDITIONAL:
                if cls.condition_matches(
                    block.condition,
                    level,
                ):
                    result.append(
                        cls.render(
                            block.children,
                            level,
                        )
                    )

        return "".join(result)

    @staticmethod
    def condition_matches(
        condition: Condition,
        level: str,
    ) -> bool:
        if condition == Condition.CATEGORY:
            return True

        return condition.value == level


# ============================================================
# Block dialog
# ============================================================

class BlockDialog(QDialog):
    def __init__(
        self,
        parent=None,
        block: Block | None = None,
        allowed_conditional=True,
    ):
        super().__init__(parent)

        self.setWindowTitle(
            "Edit block"
            if block
            else "Add block"
        )

        self.resize(500, 220)

        self.block = block

        layout = QVBoxLayout(self)

        form = QFormLayout()
        layout.addLayout(form)

        self.type_combo = QComboBox()

        self.type_combo.addItem(
            "Text",
            BlockType.TEXT,
        )

        self.type_combo.addItem(
            "Placeholder",
            BlockType.PLACEHOLDER,
        )

        self.type_combo.addItem(
            "Time",
            BlockType.TIME,
        )

        if allowed_conditional:
            self.type_combo.addItem(
                "Conditional",
                BlockType.CONDITIONAL,
            )

        form.addRow(
            "Type:",
            self.type_combo,
        )

        self.text_edit = QLineEdit()
        form.addRow(
            "Text:",
            self.text_edit,
        )

        self.placeholder_combo = QComboBox()

        placeholders = [
            "appname",
            "category",
            "file",
            "function",
            "line",
            "message",
            "pid",
            "threadid",
            "threadname",
            "qthreadptr",
            "type",
        ]

        for placeholder in placeholders:
            self.placeholder_combo.addItem(
                placeholder,
                placeholder,
            )

        form.addRow(
            "Placeholder:",
            self.placeholder_combo,
        )

        self.time_combo = QComboBox()

        time_formats = [
            "yyyy.MM.dd h:mm:ss.zzz ttt",
            "yyyy-MM-dd HH:mm:ss.zzz",
            "yyyy-MM-dd HH:mm:ss",
            "HH:mm:ss.zzz",
            "HH:mm:ss",
            "yyyy-MM-dd",
            "dd.MM.yyyy HH:mm:ss",
        ]

        for value in time_formats:
            self.time_combo.addItem(value)

        self.time_combo.setEditable(True)

        form.addRow(
            "Time format:",
            self.time_combo,
        )

        self.condition_combo = QComboBox()

        for condition in Condition:
            self.condition_combo.addItem(
                condition.title,
                condition,
            )

        form.addRow(
            "Condition:",
            self.condition_combo,
        )

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Ok
            | QDialogButtonBox.Cancel
        )

        self.buttons.accepted.connect(
            self.accept
        )

        self.buttons.rejected.connect(
            self.reject
        )

        layout.addWidget(self.buttons)

        self.type_combo.currentIndexChanged.connect(
            self.update_visibility
        )

        if block:
            self.load_block(block)

        self.update_visibility()

    def load_block(self, block: Block):
        index = self.type_combo.findData(block.type)

        if index >= 0:
            self.type_combo.setCurrentIndex(index)

        self.text_edit.setText(block.text)

        index = self.placeholder_combo.findData(
            block.placeholder
        )

        if index >= 0:
            self.placeholder_combo.setCurrentIndex(index)

        self.time_combo.setCurrentText(
            block.time_format
        )

        if block.condition:
            index = self.condition_combo.findData(
                block.condition
            )

            if index >= 0:
                self.condition_combo.setCurrentIndex(index)

    def update_visibility(self):
        block_type = self.type_combo.currentData()

        self.text_edit.setVisible(
            block_type == BlockType.TEXT
        )

        self.placeholder_combo.setVisible(
            block_type == BlockType.PLACEHOLDER
        )

        self.time_combo.setVisible(
            block_type == BlockType.TIME
        )

        self.condition_combo.setVisible(
            block_type == BlockType.CONDITIONAL
        )

    def get_block(self) -> Block:
        block_type = self.type_combo.currentData()

        if block_type == BlockType.TEXT:
            return Block(
                type=BlockType.TEXT,
                text=self.text_edit.text(),
            )

        if block_type == BlockType.PLACEHOLDER:
            return Block(
                type=BlockType.PLACEHOLDER,
                placeholder=self.placeholder_combo.currentData(),
            )

        if block_type == BlockType.TIME:
            return Block(
                type=BlockType.TIME,
                time_format=self.time_combo.currentText(),
            )

        if block_type == BlockType.CONDITIONAL:
            return Block(
                type=BlockType.CONDITIONAL,
                condition=self.condition_combo.currentData(),
            )

        raise RuntimeError("Unknown block type")


# ============================================================
# Main window
# ============================================================

class LoggingPatternEditor(QMainWindow):
    patternChanged = Signal()

    def __init__(self):
        super().__init__()

        self.setWindowTitle(
            "Qt Logging Pattern Configurator"
        )

        self.resize(1250, 800)

        self.blocks = []

        self.create_actions()
        self.create_toolbar()
        self.create_ui()

        self.set_default_pattern()

    # --------------------------------------------------------
    # UI
    # --------------------------------------------------------

    def create_actions(self):
        self.action_new = QAction(
            "New",
            self,
        )

        self.action_new.triggered.connect(
            self.new_pattern
        )

        self.action_open = QAction(
            "Open...",
            self,
        )

        self.action_open.triggered.connect(
            self.open_pattern
        )

        self.action_save = QAction(
            "Save...",
            self,
        )

        self.action_save.triggered.connect(
            self.save_pattern
        )

        self.action_copy = QAction(
            "Copy pattern",
            self,
        )

        self.action_copy.triggered.connect(
            self.copy_pattern
        )

    def create_toolbar(self):
        toolbar = QToolBar()
        toolbar.setMovable(False)

        toolbar.addAction(
            self.action_new
        )

        toolbar.addAction(
            self.action_open
        )

        toolbar.addAction(
            self.action_save
        )

        toolbar.addSeparator()

        toolbar.addAction(
            self.action_copy
        )

        self.addToolBar(toolbar)

    def create_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)

        splitter = QSplitter(
            Qt.Horizontal
        )

        main_layout.addWidget(splitter)

        # ----------------------------------------------------
        # Left side
        # ----------------------------------------------------

        left = QWidget()
        left_layout = QVBoxLayout(left)

        title = QLabel(
            "Pattern blocks"
        )

        title.setFont(
            QFont(
                "Sans",
                14,
                QFont.Bold,
            )
        )

        left_layout.addWidget(title)

        self.tree = QTreeWidget()

        self.tree.setHeaderLabels(
            [
                "Block",
                "Value",
            ]
        )

        self.tree.setAlternatingRowColors(
            True
        )

        self.tree.itemDoubleClicked.connect(
            self.edit_selected
        )

        left_layout.addWidget(
            self.tree
        )

        buttons = QHBoxLayout()

        self.add_button = QPushButton(
            "+ Add"
        )

        self.add_button.clicked.connect(
            self.add_block
        )

        buttons.addWidget(
            self.add_button
        )

        self.edit_button = QPushButton(
            "Edit"
        )

        self.edit_button.clicked.connect(
            self.edit_selected
        )

        buttons.addWidget(
            self.edit_button
        )

        self.remove_button = QPushButton(
            "Remove"
        )

        self.remove_button.clicked.connect(
            self.remove_selected
        )

        buttons.addWidget(
            self.remove_button
        )

        left_layout.addLayout(buttons)

        move_buttons = QHBoxLayout()

        self.up_button = QPushButton(
            "↑ Move up"
        )

        self.up_button.clicked.connect(
            self.move_up
        )

        move_buttons.addWidget(
            self.up_button
        )

        self.down_button = QPushButton(
            "↓ Move down"
        )

        self.down_button.clicked.connect(
            self.move_down
        )

        move_buttons.addWidget(
            self.down_button
        )

        left_layout.addLayout(
            move_buttons
        )

        splitter.addWidget(left)

        # ----------------------------------------------------
        # Right side
        # ----------------------------------------------------

        right = QWidget()
        right_layout = QVBoxLayout(right)

        tabs = QComboBox()

        tabs.addItems(
            [
                "Visual pattern",
                "Raw pattern",
            ]
        )

        self.mode_combo = tabs

        right_layout.addWidget(
            tabs
        )

        self.raw_edit = QPlainTextEdit()

        self.raw_edit.setPlaceholderText(
            "Qt message pattern..."
        )

        self.raw_edit.setVisible(False)

        self.raw_edit.textChanged.connect(
            self.raw_changed
        )

        right_layout.addWidget(
            self.raw_edit
        )

        self.visual_container = QWidget()
        visual_layout = QVBoxLayout(
            self.visual_container
        )

        visual_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        visual_layout.addWidget(
            QLabel(
                "Generated Qt logging pattern:"
            )
        )

        self.pattern_edit = QPlainTextEdit()

        self.pattern_edit.setReadOnly(True)

        self.pattern_edit.setMaximumHeight(
            100
        )

        visual_layout.addWidget(
            self.pattern_edit
        )

        visual_layout.addWidget(
            QLabel(
                "Preview:"
            )
        )

        self.preview = QPlainTextEdit()

        self.preview.setReadOnly(True)

        visual_layout.addWidget(
            self.preview
        )

        right_layout.addWidget(
            self.visual_container
        )

        tabs.currentIndexChanged.connect(
            self.mode_changed
        )

        splitter.addWidget(right)

        splitter.setStretchFactor(
            0,
            1,
        )

        splitter.setStretchFactor(
            1,
            2,
        )

        # ----------------------------------------------------
        # Bottom
        # ----------------------------------------------------

        bottom = QHBoxLayout()

        bottom.addStretch()

        apply_button = QPushButton(
            "Apply"
        )

        apply_button.clicked.connect(
            self.apply_pattern
        )

        bottom.addWidget(
            apply_button
        )

        reset_button = QPushButton(
            "Reset"
        )

        reset_button.clicked.connect(
            self.set_default_pattern
        )

        bottom.addWidget(
            reset_button
        )

        main_layout.addLayout(
            bottom
        )

    # --------------------------------------------------------
    # Default pattern
    # --------------------------------------------------------

    def set_default_pattern(self):
        pattern = (
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

        try:
            self.blocks = PatternParser.parse(
                pattern
            )

        except ValueError as error:
            QMessageBox.critical(
                self,
                "Error",
                str(error),
            )

            self.blocks = []

        self.refresh()

    # --------------------------------------------------------
    # Model helpers
    # --------------------------------------------------------

    def current_item(self):
        return self.tree.currentItem()

    def get_block_from_item(self, item):
        if not item:
            return None

        return item.data(
            0,
            Qt.UserRole,
        )

    def get_parent_children(self, item):
        parent = item.parent()

        if parent is None:
            return self.blocks

        parent_block = self.get_block_from_item(
            parent
        )

        if parent_block is None:
            return self.blocks

        return parent_block.children

    # --------------------------------------------------------
    # Tree
    # --------------------------------------------------------

    def refresh(self):
        self.tree.clear()

        for block in self.blocks:
            self.add_tree_item(
                None,
                block,
            )

        pattern = self.generate_pattern()

        self.pattern_edit.setPlainText(
            pattern
        )

        self.raw_edit.blockSignals(True)

        self.raw_edit.setPlainText(
            pattern
        )

        self.raw_edit.blockSignals(False)

        self.update_preview()

    def add_tree_item(
        self,
        parent_item,
        block,
    ):
        if parent_item is None:
            item = QTreeWidgetItem(
                self.tree
            )
        else:
            item = QTreeWidgetItem(
                parent_item
            )

        item.setData(
            0,
            Qt.UserRole,
            block,
        )

        if block.type == BlockType.TEXT:
            item.setText(
                0,
                "Text",
            )

            item.setText(
                1,
                repr(block.text),
            )

        elif block.type == BlockType.PLACEHOLDER:
            item.setText(
                0,
                "Placeholder",
            )

            item.setText(
                1,
                f"%{{{block.placeholder}}}",
            )

        elif block.type == BlockType.TIME:
            item.setText(
                0,
                "Time",
            )

            item.setText(
                1,
                block.time_format,
            )

        elif block.type == BlockType.CONDITIONAL:
            item.setText(
                0,
                "IF",
            )

            item.setText(
                1,
                block.condition.title,
            )

            for child in block.children:
                self.add_tree_item(
                    item,
                    child,
                )

            item.setExpanded(True)

    # --------------------------------------------------------
    # Selection
    # --------------------------------------------------------

    def selected_block_and_list(self):
        item = self.current_item()

        if item is None:
            return None, None, -1

        block = self.get_block_from_item(
            item
        )

        children = self.get_parent_children(
            item
        )

        try:
            index = children.index(
                block
            )

        except ValueError:
            return None, None, -1

        return block, children, index

    # --------------------------------------------------------
    # Add
    # --------------------------------------------------------

    def add_block(self):
        selected = self.current_item()

        # If a conditional block is selected,
        # add the new block inside it.
        if selected:
            selected_block = self.get_block_from_item(
                selected
            )

            if (
                selected_block
                and selected_block.type
                == BlockType.CONDITIONAL
            ):
                dialog = BlockDialog(
                    self
                )

                if dialog.exec() == QDialog.Accepted:
                    block = dialog.get_block()

                    selected_block.children.append(
                        block
                    )

                    self.refresh()

                return

        dialog = BlockDialog(
            self
        )

        if dialog.exec() != QDialog.Accepted:
            return

        block = dialog.get_block()

        if selected:
            _, children, index = (
                self.selected_block_and_list()
            )

            children.insert(
                index + 1,
                block,
            )

        else:
            self.blocks.append(
                block
            )

        self.refresh()

    # --------------------------------------------------------
    # Edit
    # --------------------------------------------------------

    def edit_selected(self):
        item = self.current_item()

        if item is None:
            return

        block = self.get_block_from_item(
            item
        )

        if block is None:
            return

        dialog = BlockDialog(
            self,
            block,
        )

        if dialog.exec() != QDialog.Accepted:
            return

        new_block = dialog.get_block()

        # Preserve children when changing
        # a conditional block.
        if (
            block.type == BlockType.CONDITIONAL
            and new_block.type == BlockType.CONDITIONAL
        ):
            new_block.children = block.children

        parent = item.parent()

        children = (
            self.blocks
            if parent is None
            else self.get_block_from_item(
                parent
            ).children
        )

        index = children.index(
            block
        )

        children[index] = new_block

        self.refresh()

    # --------------------------------------------------------
    # Remove
    # --------------------------------------------------------

    def remove_selected(self):
        block, children, index = (
            self.selected_block_and_list()
        )

        if block is None:
            return

        answer = QMessageBox.question(
            self,
            "Remove block",
            "Remove selected block?",
        )

        if answer != QMessageBox.Yes:
            return

        del children[index]

        self.refresh()

    # --------------------------------------------------------
    # Move
    # --------------------------------------------------------

    def move_up(self):
        block, children, index = (
            self.selected_block_and_list()
        )

        if block is None or index <= 0:
            return

        children[index - 1], children[index] = (
            children[index],
            children[index - 1],
        )

        self.refresh()

    def move_down(self):
        block, children, index = (
            self.selected_block_and_list()
        )

        if block is None:
            return

        if index >= len(children) - 1:
            return

        children[index + 1], children[index] = (
            children[index],
            children[index + 1],
        )

        self.refresh()

    # --------------------------------------------------------
    # Pattern generation
    # --------------------------------------------------------

    def generate_pattern(self):
        return "".join(
            block.to_pattern()
            for block in self.blocks
        )

    # --------------------------------------------------------
    # Raw mode
    # --------------------------------------------------------

    def mode_changed(self, index):
        if index == 0:
            self.visual_container.setVisible(
                True
            )

            self.raw_edit.setVisible(
                False
            )

        else:
            self.visual_container.setVisible(
                False
            )

            self.raw_edit.setVisible(
                True
            )

    def raw_changed(self):
        if self.mode_combo.currentIndex() != 1:
            return

        pattern = self.raw_edit.toPlainText()

        try:
            blocks = PatternParser.parse(
                pattern
            )

        except ValueError:
            return

        self.blocks = blocks

        self.tree.clear()

        for block in self.blocks:
            self.add_tree_item(
                None,
                block,
            )

        self.pattern_edit.setPlainText(
            pattern
        )

        self.update_preview()

    # --------------------------------------------------------
    # Preview
    # --------------------------------------------------------

    def update_preview(self):
        pattern = self.generate_pattern()

        levels = [
            "debug",
            "info",
            "warning",
            "critical",
            "fatal",
        ]

        lines = []

        for level in levels:
            rendered = PreviewGenerator.render(
                self.blocks,
                level,
            )

            lines.append(
                f"{level.upper():<9} {rendered}"
            )

        self.preview.setPlainText(
            "\n".join(lines)
        )

    # --------------------------------------------------------
    # Apply
    # --------------------------------------------------------

    def apply_pattern(self):
        pattern = self.generate_pattern()

        QApplication.clipboard().setText(
            pattern
        )

        QMessageBox.information(
            self,
            "Pattern applied",
            "The generated pattern has been copied "
            "to the clipboard.\n\n"
            "In a Qt application it can be applied with:\n\n"
            "qSetMessagePattern(pattern);",
        )

    # --------------------------------------------------------
    # Clipboard
    # --------------------------------------------------------

    def copy_pattern(self):
        QApplication.clipboard().setText(
            self.generate_pattern()
        )

        self.statusBar().showMessage(
            "Pattern copied to clipboard",
            3000,
        )

    # --------------------------------------------------------
    # New
    # --------------------------------------------------------

    def new_pattern(self):
        answer = QMessageBox.question(
            self,
            "New pattern",
            "Create an empty pattern?",
        )

        if answer != QMessageBox.Yes:
            return

        self.blocks = []

        self.refresh()

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    def save_pattern(self):
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save pattern",
            "",
            "Logging pattern (*.json);;All files (*)",
        )

        if not filename:
            return

        data = {
            "version": 1,
            "pattern": self.generate_pattern(),
            "blocks": [
                block.to_dict()
                for block in self.blocks
            ],
        }

        try:
            with open(
                filename,
                "w",
                encoding="utf-8",
            ) as file:
                json.dump(
                    data,
                    file,
                    ensure_ascii=False,
                    indent=4,
                )

        except OSError as error:
            QMessageBox.critical(
                self,
                "Save error",
                str(error),
            )

    # --------------------------------------------------------
    # Open
    # --------------------------------------------------------

    def open_pattern(self):
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Open pattern",
            "",
            "Logging pattern (*.json);;All files (*)",
        )

        if not filename:
            return

        try:
            with open(
                filename,
                "r",
                encoding="utf-8",
            ) as file:
                data = json.load(file)

            if "blocks" in data:
                self.blocks = [
                    Block.from_dict(block)
                    for block in data["blocks"]
                ]

            elif "pattern" in data:
                self.blocks = PatternParser.parse(
                    data["pattern"]
                )

            else:
                raise ValueError(
                    "Invalid pattern file"
                )

            self.refresh()

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


# ============================================================
# Main
# ============================================================

def main():
    app = QApplication(sys.argv)

    app.setApplicationName(
        "Qt Logging Pattern Configurator"
    )

    app.setOrganizationName(
        "Technohamster"
    )

    window = LoggingPatternEditor()
    window.show()

    sys.exit(
        app.exec()
    )


if __name__ == "__main__":
    main()