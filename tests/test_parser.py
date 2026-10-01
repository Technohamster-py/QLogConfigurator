from app.core.parser import PatternParser


def test_simple_pattern():
    parser = PatternParser()

    blocks = parser.parse(
        "[%{message}]"
    )

    assert len(blocks) == 3

    assert blocks[0].text == "["
    assert blocks[1].placeholder == "message"
    assert blocks[2].text == "]"


def test_conditional():
    parser = PatternParser()

    blocks = parser.parse(
        "%{if-debug}D%{endif}"
    )

    assert len(blocks) == 1

    block = blocks[0]

    assert block.condition.value == "debug"

    assert len(block.children) == 1

    assert block.children[0].text == "D"


def test_nested_conditionals():
    parser = PatternParser()

    pattern = (
        "%{if-category}"
        "A"
        "%{if-debug}"
        "B"
        "%{endif}"
        "%{endif}"
    )

    blocks = parser.parse(
        pattern
    )

    assert blocks[0].condition.value == "category"

    nested = blocks[0].children[1]

    assert nested.condition.value == "debug"


def test_unclosed_condition():
    parser = PatternParser()

    try:
        parser.parse(
            "%{if-debug}D"
        )

        assert False

    except ValueError:
        assert True