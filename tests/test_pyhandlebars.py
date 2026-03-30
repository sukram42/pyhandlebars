import timeit

import pytest
from pydantic import BaseModel

from pyhandlebars import (
    FormatError,
    HelperError,
    PyHandlebars,
    Template,
    TemplateParseError,
)


def test_invalid_template_raises_parse_error():
    with pytest.raises(TemplateParseError):
        Template("{{#if}}")  # missing closing tag


def test_from_file_missing_file_raises_parse_error(tmp_path):
    with pytest.raises(TemplateParseError):
        Template.from_file(tmp_path / "nonexistent.hbs")


def test_format_accepts_dict():
    t: Template[dict] = Template("hello {{name}}")
    assert t.format({"name": "world"}) == "hello world"


def test_format_accepts_float():
    t: Template[dict] = Template("{{price}}")
    assert t.format({"price": 3.14}) == "3.14"


def test_format_accepts_tuple():
    t: Template[dict] = Template("{{#each items}}{{this}} {{/each}}")
    assert t.format({"items": ("a", "b", "c")}) == "a b c "


def test_format_accepts_pydantic_model():
    class Person(BaseModel):
        name: str
        age: int

    person = Person(name="Alice", age=30)
    t: Template[Person] = Template("{{name}} is {{age}}")
    assert t.format(person) == "Alice is 30"


def test_strict_mode_raises_format_error_for_missing_variable():
    client = PyHandlebars(strict_mode=True)
    t: Template[dict] = Template("{{missing_var}}", client=client)
    with pytest.raises(FormatError):
        t.format({})


def test_helper_error_propagates():
    def bad_helper(params, data):
        raise ValueError("something went wrong")

    client = PyHandlebars()
    client.register_helper("boom", bad_helper)
    t: Template[dict] = Template("{{boom}}", client=client)
    with pytest.raises(HelperError):
        t.format({})


def test_helper_return_value_used_in_output():
    def shout(params, data):
        return params[0].upper()

    client = PyHandlebars()
    client.register_helper("shout", shout)
    t: Template[dict] = Template("{{shout name}}", client=client)
    assert t.format({"name": "hello"}) == "HELLO"


def test_helper_decorator():
    client = PyHandlebars()

    @client.helper(name="shout")
    def shout(params, data):
        return params[0].upper() + "!"

    t1: Template[dict] = Template("{{shout name}}", client=client)
    assert t1.format({"name": "hello"}) == "HELLO!"

    @client.helper()
    def shouty(params, data):
        return params[0].upper() + "?"

    t2: Template[dict] = Template("{{shouty name}}", client=client)
    assert t2.format({"name": "hello"}) == "HELLO?"


def test_benchmark_format_dict():
    n = 1_000
    t: Template[dict] = Template("hello {{name}}")
    elapsed = timeit.timeit(lambda: t.format({"name": "world"}), number=n)
    mean = elapsed / n
    print(f"\nformat (dict) mean: {mean * 1000:.4f}ms")
    assert mean < 0.00005


def test_benchmark_format_pydantic():
    class Person(BaseModel):
        name: str
        age: int

    n = 1_000
    person = Person(name="Alice", age=30)
    t: Template[Person] = Template("{{name}} is {{age}}")
    elapsed = timeit.timeit(lambda: t.format(person), number=n)
    mean = elapsed / n
    print(f"\nformat (pydantic) mean: {mean * 1000:.4f}ms")
    assert mean < 0.00005
