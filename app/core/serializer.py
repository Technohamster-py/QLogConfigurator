from __future__ import annotations

import json
from pathlib import Path

from app.core.pattern import (
    Block,
    BlockType,
    Condition,
)


class PatternSerializer:

    VERSION = 1

    @staticmethod
    def block_to_dict(
        block: Block,
    ) -> dict:
        return {
            "type": block.type.value,
            "text": block.text,
            "placeholder": block.placeholder,
            "time_format": block.time_format,
            "condition": (
                block.condition.value
                if block.condition
                else None
            ),
            "children": [
                PatternSerializer.block_to_dict(
                    child
                )
                for child in block.children
            ],
        }

    @staticmethod
    def block_from_dict(
        data: dict,
    ) -> Block:
        condition = data.get(
            "condition"
        )

        return Block(
            type=BlockType(
                data["type"]
            ),
            text=data.get(
                "text",
                "",
            ),
            placeholder=data.get(
                "placeholder",
                "",
            ),
            time_format=data.get(
                "time_format",
                "",
            ),
            condition=(
                Condition(condition)
                if condition
                else None
            ),
            children=[
                PatternSerializer.block_from_dict(
                    child
                )
                for child in data.get(
                    "children",
                    [],
                )
            ],
        )

    @classmethod
    def save(
        cls,
        filename: str | Path,
        blocks: list[Block],
    ) -> None:
        path = Path(filename)

        data = {
            "version": cls.VERSION,
            "blocks": [
                cls.block_to_dict(block)
                for block in blocks
            ],
            "pattern": "".join(
                block.to_pattern()
                for block in blocks
            ),
        }

        path.write_text(
            json.dumps(
                data,
                ensure_ascii=False,
                indent=4,
            ),
            encoding="utf-8",
        )

    @classmethod
    def load(
        cls,
        filename: str | Path,
    ) -> list[Block]:
        path = Path(filename)

        data = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )

        return [
            cls.block_from_dict(block)
            for block in data["blocks"]
        ]