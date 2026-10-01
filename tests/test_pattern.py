from app.core.pattern import (
    Block,
    BlockType,
    Condition,
)


def test_text():
    block = Block(
        type=BlockType.TEXT,
        text="Hello",
    )

    assert block.to_pattern() == "Hello"


def test_placeholder():
    block = Block(
        type=BlockType.PLACEHOLDER,
        placeholder="message",
    )

    assert block.to_pattern() == (
        "%{message}"
    )


def test_time():
    block = Block(
        type=BlockType.TIME,
        time_format=(
            "yyyy.MM.dd h:mm:ss.zzz ttt"
        ),
    )

    assert block.to_pattern() == (
        "%{time yyyy.MM.dd h:mm:ss.zzz ttt}"
    )


def test_conditional():
    block = Block(
        type=BlockType.CONDITIONAL,
        condition=Condition.DEBUG,
        children=[
            Block(
                type=BlockType.TEXT,
                text="D",
            )
        ],
    )

    assert block.to_pattern() == (
        "%{if-debug}D%{endif}"
    )