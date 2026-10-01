from app.core.pattern import (
    Block,
    BlockType,
    Condition,
)


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
                result.append(
                    block.text
                )

            elif block.type == BlockType.PLACEHOLDER:
                if block.placeholder == "type":
                    result.append(
                        level.upper()
                    )
                else:
                    result.append(
                        cls.SAMPLE_VALUES.get(
                            block.placeholder,
                            f"<{block.placeholder}>",
                        )
                    )

            elif block.type == BlockType.TIME:
                result.append(
                    "2026.10.01 10:30:00.123 CEST"
                )

            elif block.type == BlockType.CONDITIONAL:
                if cls.matches(
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
    def matches(
        condition: Condition | None,
        level: str,
    ) -> bool:
        if condition == Condition.CATEGORY:
            return True

        return (
            condition is not None
            and condition.value == level
        )