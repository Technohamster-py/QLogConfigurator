from __future__ import annotations

import re

from app.core.pattern import (
    Block,
    BlockType,
    Condition,
    PLACEHOLDERS,
)


class PatternParser:
    TOKEN_RE = re.compile(
        r"%\{([^}]*)\}"
    )

    CONDITIONS = {
        condition.value: condition
        for condition in Condition
    }

    def parse(
        self,
        pattern: str,
    ) -> list[Block]:
        root: list[Block] = []

        stack: list[list[Block]] = [
            root
        ]

        position = 0

        for match in self.TOKEN_RE.finditer(
            pattern
        ):
            if match.start() > position:
                stack[-1].append(
                    Block(
                        type=BlockType.TEXT,
                        text=pattern[
                            position:match.start()
                        ],
                    )
                )

            token = match.group(1)

            if token.startswith("if-"):
                condition_name = token[3:]

                condition = self.CONDITIONS.get(
                    condition_name
                )

                if condition is None:
                    raise ValueError(
                        f"Unknown condition: "
                        f"{condition_name}"
                    )

                block = Block(
                    type=BlockType.CONDITIONAL,
                    condition=condition,
                )

                stack[-1].append(block)

                stack.append(
                    block.children
                )

            elif token == "endif":
                if len(stack) == 1:
                    raise ValueError(
                        "Unexpected %{endif}"
                    )

                stack.pop()

            elif token.startswith("time"):
                time_format = (
                    token[4:].strip()
                )

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

            elif token in PLACEHOLDERS:
                stack[-1].append(
                    Block(
                        type=BlockType.PLACEHOLDER,
                        placeholder=token,
                    )
                )

            else:
                raise ValueError(
                    f"Unknown Qt logging token: "
                    f"%{{{token}}}"
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