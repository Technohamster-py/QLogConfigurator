from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


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
    def title(self) -> str:
        return {
            Condition.DEBUG: "Debug",
            Condition.INFO: "Info",
            Condition.WARNING: "Warning",
            Condition.CRITICAL: "Critical",
            Condition.FATAL: "Fatal",
            Condition.CATEGORY: "Category",
        }[self]


PLACEHOLDERS = (
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
)


@dataclass
class Block:
    type: BlockType

    text: str = ""
    placeholder: str = ""
    time_format: str = ""
    condition: Condition | None = None

    children: list[Block] = field(
        default_factory=list
    )

    def to_pattern(self) -> str:
        if self.type == BlockType.TEXT:
            return self.text

        if self.type == BlockType.PLACEHOLDER:
            return f"%{{{self.placeholder}}}"

        if self.type == BlockType.TIME:
            return f"%{{time {self.time_format}}}"

        if self.type == BlockType.CONDITIONAL:
            if self.condition is None:
                raise ValueError(
                    "Conditional block has no condition"
                )

            content = "".join(
                child.to_pattern()
                for child in self.children
            )

            return (
                f"%{{if-{self.condition.value}}}"
                f"{content}"
                f"%{{endif}}"
            )

        raise ValueError(
            f"Unsupported block type: {self.type}"
        )

    def is_container(self) -> bool:
        return self.type == BlockType.CONDITIONAL

    def display_name(self) -> str:
        if self.type == BlockType.TEXT:
            return "Text"

        if self.type == BlockType.PLACEHOLDER:
            return "Placeholder"

        if self.type == BlockType.TIME:
            return "Time"

        if self.type == BlockType.CONDITIONAL:
            return "IF"

        return self.type.value

    def display_value(self) -> str:
        if self.type == BlockType.TEXT:
            return repr(self.text)

        if self.type == BlockType.PLACEHOLDER:
            return f"%{{{self.placeholder}}}"

        if self.type == BlockType.TIME:
            return self.time_format

        if self.type == BlockType.CONDITIONAL:
            return (
                self.condition.title
                if self.condition
                else "<invalid>"
            )

        return ""