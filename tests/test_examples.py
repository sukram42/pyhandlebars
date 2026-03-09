from pathlib import Path

from pyhandlebars import PyHandlebars


def test_simple_template_creation():
    from pyhandlebars import Template

    t: Template[dict] = Template("Hello {{name}}")
    rendered_text = t.format({"name": "world"})

    assert rendered_text == "Hello world"


def test_simple_pydantic_support():
    from pyhandlebars import Template
    from pydantic import BaseModel

    class Person(BaseModel):
        name: str

    t: Template[Person] = Template("This is {{name}}!")
    rendered_text = t.format(Person(name="Alice"))
    assert rendered_text == "This is Alice!"

def test_template_from_file():
    from pyhandlebars import Template

    t: Template[dict] = Template.from_file(Path("tests/test.hbs"))
    rendered_text = t.format({"name": "world"})
    assert rendered_text == "Hallo world"


def test_template_with_pydantic_model():
    from pyhandlebars import Template
    from pydantic import BaseModel

    class Person(BaseModel):
        name: str
        age: int

    person = Person(name="Alice", age=30)
    t: Template[Person] = Template("{{name}} is {{age}}")
    rendered_text = t.format(person)
    assert rendered_text == "Alice is 30"


def test_raw_string():
    from pyhandlebars import Template

    t: Template[dict] = Template("Raw string with {{{{raw}}}} {{curly braces}} {{{{/raw}}}}")
    rendered_text = t.format({})
    print(rendered_text)
    assert rendered_text == "Raw string with {{curly braces}} "


def test_if_statement():
    from pyhandlebars import Template

    t: Template[dict] = Template("{{#if condition}}Condition is true{{else}}Condition is false{{/if}}")

    assert t.format({"condition": True}) == "Condition is true"
    assert t.format({"condition": False}) == "Condition is false"


def test_unless_statement():
    from pyhandlebars import Template

    t: Template[dict] = Template("{{#unless condition}}Condition is false{{else}}Condition is true{{/unless}}")

    assert t.format({"condition": True}) == "Condition is true"
    assert t.format({"condition": False}) == "Condition is false"


def test_each_statement():
    from pyhandlebars import Template

    t: Template[dict] = Template("{{#each items}}{{this}} {{/each}}")

    assert t.format({"items": ["a", "b", "c"]}) == "a b c "


def test_with_statement():
    from pyhandlebars import Template

    t: Template[dict] = Template("{{#with person}}{{name}} is {{age}}{{/with}}")

    assert t.format({"person": {"name": "Alice", "age": 30}}) == "Alice is 30"


def test_easy_lookup_statement():
    from pyhandlebars import Template

    t: Template[dict] = Template("{{lookup people 0}}")

    assert t.format({"people": ["Alice", "Bob"]}) == "Alice"


def test_complex_lookup_statement():
    # https://handlebarsjs.com/guide/builtin-helpers.html#lookup

    from pyhandlebars import Template

    t: Template[dict] = Template("""
{{#each persons as | person |}}
  {{name}} lives in {{#with (lookup ../cities [resident-in])~}}
    {{name}} ({{country}})
  {{/with}}
{{/each}}""")

    res = t.format(
        {
            "persons": [{"name": "Alice", "resident-in": "dortmund"}],
            "cities": {
                "dortmund": {"name": "Dortmund", "country": "Germany"},
                "paris": {"name": "Paris", "country": "France"},
            },
        }
    )
    assert res.strip() == """Alice lives in Dortmund (Germany)""".strip()


def test_include_templates():
    from pyhandlebars import Template

    client = PyHandlebars()

    # The connection is done via the shared client and specified name.
    _ = Template("Wuhuu its {{name}}", name="name", client=client)
    t1: Template[dict] = Template("person of the day: {{> name}}", client=client)

    # Register the included template

    res = t1.format({"name": "Alice"})
    assert res == "person of the day: Wuhuu its Alice"


def test_len_statement(caplog):
    from pyhandlebars import Template

    t: Template[dict] = Template("{{len messages}}")

    # Just check that it doesn't raise an error
    assert t.format({"messages": ["This is a message", "another message"]}) == "2"


def test_bool_operators():
    from pyhandlebars import Template

    t: Template[dict] = Template("{{#if (eq name 'Alice')}}Hi Alice!{{/if}}")
    assert t.format({"name": "Alice"}) == "Hi Alice!"

    u: Template[dict] = Template("{{#if (and (eq name 'Alice') (gte age 30))}}Oh Alice is older than 30!{{/if}}")
    assert u.format({"name": "Alice", "age": 31}) == "Oh Alice is older than 30!"
    # Same works with eq, ne, gt, gte, lt, lte, and, or, not


def test_custom_helper():
    # Custom helpers can help to extend the functionality. However, they are not as fast as the built-in helpers,
    # so they should be used with care. Sadly, for the context, we can only provide a dict but not the full Pydantic model.
    # The reason for this is the shared client.
    from pyhandlebars import PyHandlebars, Template

    def shout(params: list[str], context: dict):
        return f"{params[0].upper()} from {context['location']}"

    client = PyHandlebars()
    client.register_helper("shout", shout)

    t: Template[dict] = Template("{{shout name}}", client=client)
    assert t.format({"name": "Alice", "location": "Wonderland"}) == "ALICE from Wonderland"
