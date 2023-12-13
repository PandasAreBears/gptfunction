from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union, get_args, no_type_check
import logging
import docstring_parser
from docstring_parser.common import DocstringParam
from dataclasses import dataclass


class GPTFunction:
    """
    A class representing a GPT callable function. GPT functions are defined using a JSON
    schema which GPT uses to make a call.

    GPT functions created using this wrapper must follow a strict definition.
    1. Parameters should use type hinting, and can only be of the following types:
        1. str
        2. int
        3. float
        4. typing.Literal
        5. a subclass of Enum (with string values)

    2. The doc string should begin with a concise description of what the function does.

    3. Parameters should be documented using the rST standard format.

    A GPT function may optionally return a string which will be passed to GPT as the result. If no
    value is returned then some arbitrary success string will be sent.

    :example:
    ```py
    def output_user(name: str, age: int) -> None:
        \"""
        Outputs a user's name and age to the console.

        :param name: The name of the user.
        :param age: The age of the user.
        \"""
        print(f"Name: {name}, Age: {age}")

    my_gpt_func = GPTFunction(output_user)

    gpt_tools = [my_gpt_func.schema()]
    ```
    """

    @dataclass
    class _FunctionParam:
        name: str
        typing: type
        description: str

    def __init__(self, func: Callable[..., Any]) -> None:
        self.func = func

    @no_type_check
    def __call__(self, *args, **kwargs) -> Optional[str]:
        result = self.func(*args, **kwargs)

        # GPT expects function calls to return a string.
        if isinstance(result, str):
            return result

        if getattr(result, "__str__"):
            return str(result)

        return ""

    def schema(self) -> object:
        """
        Generates the schema required for passing a function to GPT.
        """
        docstring = docstring_parser.parse(self.func.__doc__)
        return {
            "type": "function",
            "function": {
                "name": self.func.__name__,
                "description": docstring.short_description,
                "parameters": GPTFunction._parse_params(
                    GPTFunction._create_function_params(
                        self.func.__annotations__, docstring.params
                    ),
                ),
            },
        }

    def name(self) -> str:
        """
        Get the name of this function.

        :return: The function name.
        """
        return self.func.__name__

    def description(self) -> str:
        """
        Get the description of this function.

        :return: The function description
        """
        return docstring_parser.parse(self.func.__doc__).short_description

    @staticmethod
    def _create_function_params(
        annotations: Dict[str, type], docstring_params: List[DocstringParam]
    ) -> List[_FunctionParam]:
        """
        Combines annotation data with param documentation into a unified data storing the GPT
        function's parameters in order.

        :param annotations: The type annotation of the function.
        :param docstring_params: The docstring of the parameters of the function.
        :return: An list of the unified function data in order.

        :example:
        ```python
        def my_func(a: int, b: int) -> int:
            \"""
            My function.

            :param a: This is param a!
            :param b: Param b
                      spans multiple lines.
            :return: An int.
            \"""
            return a + b

        import docstring_parser

        docstring_params = docstring_parser.parse(my_func.__doc__)

        function_params = create_function_params(my_func.__annotations__, docstring_params)

        assert len(function_params) == 2
        assert function_params[0].name == "a"
        assert function_params[0].typing == str
        assert function_params[0].description == "This is param a!"
        ```
        """
        if "return" in annotations:
            del annotations["return"]

        keyed_docstring_params = {p.arg_name: p for p in docstring_params}

        function_params = []
        for key in annotations:
            desc = ""
            if key in keyed_docstring_params:
                desc = keyed_docstring_params[key].description
            else:
                logging.warning(
                    f"Function param {key} has no docstring description. Add a docstring description for more accurate use by GPT."
                )

            function_params.append(
                GPTFunction._FunctionParam(key, annotations[key], desc)
            )

        return function_params

    @staticmethod
    def _parse_params(params: List[_FunctionParam]) -> Dict[str, Any]:
        """
        Converts a function's params into a 'parameters' object used by the function calling schema.
        :param params: The function parameters to parse into the schema.
        :return: The parameters part of the function calling schema.
        """
        schema_params: Dict[str, Any] = {}
        for param in params:
            schema_params |= {
                param.name: GPTFunction._parse_param_type(param.typing)
                | {"description": param.description}
            }

        return {"type": "object", "properties": schema_params}

    @staticmethod
    def _parse_param_type(
        param_type: Union[type, object],
    ) -> Dict[str, Union[str, List[str]]]:
        """
        Converts a `typing` hint into a param object used by the function calling schema.
        :param param_type: The type of the parameter.
        :return: The parameter part of the function calling schema.

        Example1
        ```python
        def my_func(a: int, b: str) -> None:
            pass

        a_param = parse_param_type(my_func.__annotations__[0])

        assert a_param == {"type": "int"}
        ```

        Example2
        ```python
        class Fruit:
            ORANGE = "orange"
            BANANA = "banana"

        def my_func(fruit: Fruit) -> None:
            pass


        fruit_param = parse_param_type(my_func.__annotations[0])

        assert fruit_param == {"type": "string", "enum": ["orange", "banana"]}
        ```

        """
        if param_type == str:
            return {"type": "string"}

        elif param_type == int:
            return {"type": "int"}

        elif param_type == float:
            return {"type": "float"}

        elif types := get_args(param_type):
            return {"type": "string", "enum": list(types)}

        elif isinstance(param_type, type) and issubclass(param_type, Enum):
            return {"type": "string", "enum": [e.value for e in param_type]}

        raise ValueError(
            f"Unexpected type found while parsing parameter type: {param_type}"
        )


def gptfunction(func: Callable[..., Any]) -> GPTFunction:
    return GPTFunction(func)
