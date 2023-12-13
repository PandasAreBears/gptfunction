from typing import no_type_check
import pytest

from gptfunction import gptfunction, GPTFunction


class TestParseParamType:
    def test_unexpected_type_raises_error(self) -> None:
        with pytest.raises(ValueError):
            GPTFunction._parse_param_type(dict)

        with pytest.raises(ValueError):
            GPTFunction._parse_param_type(bool)

        with pytest.raises(ValueError):
            GPTFunction._parse_param_type(list)

    def test_return_correct_primitive_types(self) -> None:
        assert GPTFunction._parse_param_type(int) == {"type": "int"}
        assert GPTFunction._parse_param_type(str) == {"type": "string"}
        assert GPTFunction._parse_param_type(float) == {"type": "float"}

    def test_handles_literal_type(self) -> None:
        from typing import Literal

        result = GPTFunction._parse_param_type(Literal["one", "two", "three"])

        assert result == {"type": "string", "enum": ["one", "two", "three"]}

    def test_handles_enum_type(self) -> None:
        from enum import Enum

        class Number(Enum):
            ONE = "one"
            TWO = "two"
            THREE = "three"

        result = GPTFunction._parse_param_type(Number)

        assert result == {"type": "string", "enum": ["one", "two", "three"]}


class TestCreateFunctionParams:
    def test_handles_function_with_no_params(self) -> None:
        import docstring_parser

        def no_param_function() -> None:
            """
            I'm a function with no params!
            """

        docstring = docstring_parser.parse(no_param_function.__doc__)
        params = GPTFunction._create_function_params(
            no_param_function.__annotations__, docstring.params
        )

        assert len(params) == 0

    def test_handles_correct_function_parameters(self) -> None:
        import docstring_parser

        def my_func(a: int, b: int) -> int:
            """
            I'm a function that does something!

            :param a: Param a does a thing.
            :param b: b description
                      spans multiple lines.
            :return: Something.
            """
            return a + b

        docstring = docstring_parser.parse(my_func.__doc__)
        params = GPTFunction._create_function_params(
            my_func.__annotations__, docstring.params
        )

        assert len(params) == 2

        assert params[0].name == "a"
        assert params[0].typing == int
        assert params[0].description == "Param a does a thing."

        assert params[1].name == "b"
        assert params[1].typing == int
        assert params[1].description == "b description\nspans multiple lines."

    def test_handles_undocumented_parameter(self) -> None:
        import docstring_parser

        def my_func(a: int, b: int) -> int:
            """
            Lol no docs for you
            """
            return a + b

        docstring = docstring_parser.parse(my_func.__doc__)
        params = GPTFunction._create_function_params(
            my_func.__annotations__, docstring.params
        )

        assert len(params) == 2

        assert params[0].name == "a"
        assert params[0].typing == int
        assert params[0].description == ""

        assert params[1].name == "b"
        assert params[1].typing == int
        assert params[1].description == ""

    def test_errors_with_no_type_annotations(self) -> None:
        import docstring_parser

        @no_type_check
        def my_func(a, b):
            """
            I can write docstring but not type annotations.

            :param a: Param a does a thing.
            :param b: b description
                      spans multiple lines.
            :return: Something.
            """
            return a + b

        docstring = docstring_parser.parse(my_func.__doc__)
        params = GPTFunction._create_function_params(
            my_func.__annotations__, docstring.params
        )

        assert len(params) == 0


class TestParseParams:
    def test_handles_function_with_no_params(self) -> None:
        assert GPTFunction._parse_params([]) == {"type": "object", "properties": {}}

    def test_handles_function_with_params(self) -> None:
        params = [
            GPTFunction._FunctionParam("a", int, "this is a"),
            GPTFunction._FunctionParam("b", str, "this is b"),
        ]

        result = GPTFunction._parse_params(params)

        assert result == {
            "type": "object",
            "properties": {
                "a": {"type": "int", "description": "this is a"},
                "b": {"type": "string", "description": "this is b"},
            },
        }


class TestSchema:
    def test_handles_func_with_all_param_types(self) -> None:
        from typing import Literal
        from enum import Enum

        class Fruit(Enum):
            ORANGE = "orange"
            APPLE = "apple"

        def my_complex_func(
            a: int, b: str, c: float, d: Fruit, e: Literal["one", "two", "three"]
        ) -> None:
            """
            This function does something complicated.

            :param a: this is a.
            :param b: this is b.
            :param c: this is c.
            :param d: this is d.
            :param e: this is e.
            :return: None.
            """
            return

        gpt_func = GPTFunction(my_complex_func)
        schema = gpt_func.schema()

        expected = {
            "type": "function",
            "function": {
                "name": "my_complex_func",
                "description": "This function does something complicated.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "a": {"type": "int", "description": "this is a."},
                        "b": {"type": "string", "description": "this is b."},
                        "c": {"type": "float", "description": "this is c."},
                        "d": {
                            "type": "string",
                            "description": "this is d.",
                            "enum": ["orange", "apple"],
                        },
                        "e": {
                            "type": "string",
                            "description": "this is e.",
                            "enum": ["one", "two", "three"],
                        },
                    },
                },
            },
        }

        assert schema == expected


class TestDecorator:
    def test_decorator_on_func(self) -> None:
        RET_VAL = 5

        @gptfunction
        def my_func(a: int, b: str) -> int:
            """
            This is my func.

            :param a: this is a.
            :param b: this is b.
            :return: integer
            """
            return RET_VAL

        assert my_func(1, "r") == str(RET_VAL)

        expected_schema = {
            "type": "function",
            "function": {
                "name": "my_func",
                "description": "This is my func.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "a": {"type": "int", "description": "this is a."},
                        "b": {"type": "string", "description": "this is b."},
                    },
                },
            },
        }
        assert my_func.schema() == expected_schema

        assert my_func(5, "b") == str(RET_VAL)
