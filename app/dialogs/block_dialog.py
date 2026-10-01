from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QVBoxLayout,
)

from app.core.pattern import (
    Block,
    BlockType,
    Condition,
    PLACEHOLDERS,
)


class BlockDialog(QDialog):

    def __init__(
        self,
        parent=None,
        block: Block | None = None,
    ):
        super().__init__(parent)

        self.setWindowTitle(
            "Edit block"
            if block
            else "Add block"
        )

        self.resize(
            450,
            220,
        )

        self._block = block

        layout = QVBoxLayout(
            self
        )

        form = QFormLayout()

        layout.addLayout(
            form
        )

        self.type_combo = QComboBox()

        for block_type in BlockType:
            self.type_combo.addItem(
                self.type_title(
                    block_type
                ),
                block_type,
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

        for placeholder in PLACEHOLDERS:
            self.placeholder_combo.addItem(
                placeholder
            )

        form.addRow(
            "Placeholder:",
            self.placeholder_combo,
        )

        self.time_edit = QLineEdit(
            "yyyy.MM.dd h:mm:ss.zzz ttt"
        )

        form.addRow(
            "Time format:",
            self.time_edit,
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

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok
            | QDialogButtonBox.Cancel
        )

        buttons.accepted.connect(
            self.accept
        )

        buttons.rejected.connect(
            self.reject
        )

        layout.addWidget(
            buttons
        )

        self.type_combo.currentIndexChanged.connect(
            self.update_fields
        )

        if block:
            self.load_block(block)

        self.update_fields()

    @staticmethod
    def type_title(
        block_type: BlockType,
    ) -> str:
        return {
            BlockType.TEXT: "Text",
            BlockType.PLACEHOLDER: "Placeholder",
            BlockType.TIME: "Time",
            BlockType.CONDITIONAL: "Conditional",
        }[block_type]

    def load_block(
        self,
        block: Block,
    ):
        index = self.type_combo.findData(
            block.type
        )

        if index >= 0:
            self.type_combo.setCurrentIndex(
                index
            )

        self.text_edit.setText(
            block.text
        )

        index = self.placeholder_combo.findText(
            block.placeholder
        )

        if index >= 0:
            self.placeholder_combo.setCurrentIndex(
                index
            )

        self.time_edit.setText(
            block.time_format
        )

        if block.condition:
            index = self.condition_combo.findData(
                block.condition
            )

            if index >= 0:
                self.condition_combo.setCurrentIndex(
                    index
                )

    def update_fields(self):
        block_type = (
            self.type_combo.currentData()
        )

        self.text_edit.setEnabled(
            block_type == BlockType.TEXT
        )

        self.placeholder_combo.setEnabled(
            block_type == BlockType.PLACEHOLDER
        )

        self.time_edit.setEnabled(
            block_type == BlockType.TIME
        )

        self.condition_combo.setEnabled(
            block_type == BlockType.CONDITIONAL
        )

    def block(self) -> Block:
        block_type = (
            self.type_combo.currentData()
        )

        if block_type == BlockType.TEXT:
            return Block(
                type=BlockType.TEXT,
                text=self.text_edit.text(),
            )

        if block_type == BlockType.PLACEHOLDER:
            return Block(
                type=BlockType.PLACEHOLDER,
                placeholder=(
                    self.placeholder_combo.currentText()
                ),
            )

        if block_type == BlockType.TIME:
            return Block(
                type=BlockType.TIME,
                time_format=(
                    self.time_edit.text()
                ),
            )

        return Block(
            type=BlockType.CONDITIONAL,
            condition=(
                self.condition_combo.currentData()
            ),
        )