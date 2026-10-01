from __future__ import annotations

from PySide6.QtCore import (
    QAbstractItemModel,
    QModelIndex,
    Qt,
)

from app.core.pattern import Block


class PatternModel(QAbstractItemModel):

    TYPE_ROLE = Qt.UserRole + 1
    VALUE_ROLE = Qt.UserRole + 2

    def __init__(
        self,
        blocks: list[Block] | None = None,
        parent=None,
    ):
        super().__init__(parent)

        self._blocks = (
            blocks
            if blocks is not None
            else []
        )

    # --------------------------------------------------------
    # Basic model API
    # --------------------------------------------------------

    def rowCount(
        self,
        parent=QModelIndex(),
    ) -> int:
        if not parent.isValid():
            return len(self._blocks)

        block = self.block_from_index(
            parent
        )

        if block is None:
            return 0

        return len(block.children)

    def columnCount(
        self,
        parent=QModelIndex(),
    ) -> int:
        return 2

    def data(
        self,
        index,
        role=Qt.DisplayRole,
    ):
        if not index.isValid():
            return None

        block = self.block_from_index(
            index
        )

        if block is None:
            return None

        if role == Qt.DisplayRole:
            if index.column() == 0:
                return block.display_name()

            if index.column() == 1:
                return block.display_value()

        if role == self.TYPE_ROLE:
            return block.type.value

        if role == self.VALUE_ROLE:
            return block.display_value()

        return None

    def headerData(
        self,
        section,
        orientation,
        role=Qt.DisplayRole,
    ):
        if (
            orientation == Qt.Horizontal
            and role == Qt.DisplayRole
        ):
            return (
                "Block"
                if section == 0
                else "Value"
            )

        return None

    def index(
        self,
        row,
        column,
        parent=QModelIndex(),
    ):
        if row < 0 or column < 0:
            return QModelIndex()

        if not parent.isValid():
            children = self._blocks
        else:
            parent_block = (
                self.block_from_index(
                    parent
                )
            )

            if parent_block is None:
                return QModelIndex()

            children = parent_block.children

        if row >= len(children):
            return QModelIndex()

        return self.createIndex(
            row,
            column,
            children[row],
        )

    def parent(
        self,
        index,
    ):
        if not index.isValid():
            return QModelIndex()

        block = self.block_from_index(
            index
        )

        if block is None:
            return QModelIndex()

        parent_block = self.find_parent(
            block
        )

        if parent_block is None:
            return QModelIndex()

        grandparent = self.find_parent(
            parent_block
        )

        siblings = (
            self._blocks
            if grandparent is None
            else grandparent.children
        )

        row = siblings.index(
            parent_block
        )

        return self.createIndex(
            row,
            0,
            parent_block,
        )

    # --------------------------------------------------------
    # Access
    # --------------------------------------------------------

    def block_from_index(
        self,
        index: QModelIndex,
    ) -> Block | None:
        if not index.isValid():
            return None

        return index.internalPointer()

    def blocks(self) -> list[Block]:
        return self._blocks

    def set_blocks(
        self,
        blocks: list[Block],
    ):
        self.beginResetModel()

        self._blocks = blocks

        self.endResetModel()

    # --------------------------------------------------------
    # Tree helpers
    # --------------------------------------------------------

    def find_parent(
        self,
        target: Block,
        blocks=None,
    ) -> Block | None:
        if blocks is None:
            blocks = self._blocks

        for block in blocks:
            if target in block.children:
                return block

            parent = self.find_parent(
                target,
                block.children,
            )

            if parent is not None:
                return parent

        return None

    def siblings_for(
        self,
        block: Block,
    ) -> list[Block]:
        parent = self.find_parent(
            block
        )

        return (
            self._blocks
            if parent is None
            else parent.children
        )

    # --------------------------------------------------------
    # Modification
    # --------------------------------------------------------

    def add_block(
        self,
        block: Block,
        parent: Block | None = None,
        row: int = -1,
    ):
        children = (
            self._blocks
            if parent is None
            else parent.children
        )

        if row < 0:
            row = len(children)

        parent_index = (
            QModelIndex()
            if parent is None
            else self.index_for_block(
                parent
            )
        )

        self.beginInsertRows(
            parent_index,
            row,
            row,
        )

        children.insert(
            row,
            block,
        )

        self.endInsertRows()

    def remove_block(
        self,
        block: Block,
    ):
        parent = self.find_parent(
            block
        )

        children = (
            self._blocks
            if parent is None
            else parent.children
        )

        row = children.index(
            block
        )

        parent_index = (
            QModelIndex()
            if parent is None
            else self.index_for_block(
                parent
            )
        )

        self.beginRemoveRows(
            parent_index,
            row,
            row,
        )

        children.pop(row)

        self.endRemoveRows()

    def move_block(
        self,
        block: Block,
        new_row: int,
    ) -> bool:
        children = self.siblings_for(
            block
        )

        old_row = children.index(
            block
        )

        if new_row < 0:
            return False

        if new_row >= len(children):
            return False

        if old_row == new_row:
            return False

        parent = self.find_parent(
            block
        )

        parent_index = (
            QModelIndex()
            if parent is None
            else self.index_for_block(
                parent
            )
        )

        destination = (
            new_row
            if new_row < old_row
            else new_row + 1
        )

        if not self.beginMoveRows(
            parent_index,
            old_row,
            old_row,
            parent_index,
            destination,
        ):
            return False

        children.insert(
            new_row,
            children.pop(old_row),
        )

        self.endMoveRows()

        return True

    def index_for_block(
        self,
        block: Block,
    ) -> QModelIndex:
        parent = self.find_parent(
            block
        )

        siblings = (
            self._blocks
            if parent is None
            else parent.children
        )

        try:
            row = siblings.index(
                block
            )
        except ValueError:
            return QModelIndex()

        return self.createIndex(
            row,
            0,
            block,
        )

    # --------------------------------------------------------
    # Pattern
    # --------------------------------------------------------

    def pattern(self) -> str:
        return "".join(
            block.to_pattern()
            for block in self._blocks
        )