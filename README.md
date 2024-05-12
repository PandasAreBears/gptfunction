## Overview

The `GPTFunction` Python module provides a decorator for wrapping Python functions to generate an OpenAI GPT function calling schema. This module is particularly useful for those who need to integrate Python functions with GPT in a structured and efficient manner. The decorator transforms a regular Python function into a GPT function with a JSON schema, which can then be utilized by GPT for various purposes.

## Features

- **Type Hinting and Documentation**: The module enforces type hinting for parameters, supporting types like `str`, `int`, `float`, `typing.Literal`, and subclasses of `Enum`.
- **Docstring Parsing**: It parses the function's docstring to extract descriptions, ensuring a detailed and clear schema.
- **Automatic Schema Generation**: Generates the necessary schema for GPT integration seamlessly.

## Installation

```bash
pip install gptfunction
```

## Usage

### Basic Example

```python
from gptfunction import gptfunction

@gptfunction
def output_user(name: str, age: int) -> None:
    """
    Outputs a user's name and age to the console.

    :param name: The name of the user.
    :param age: The age of the user.
    """
    print(f"Name: {name}, Age: {age}")

gpt_tools = [output_user.schema()]
```

### Advanced Usage with Enums and Literals

```python
from gptfunction import gptfunction
from enum import Enum
from typing import Literal

class Fruit(Enum):
    APPLE = 'apple'
    BANANA = 'banana'

@gptfunction
def favorite_fruit(user_name: str, fruit: Fruit, quantity: Literal[1, 2, 3]) -> str:
    """
    Returns a string stating the user's favorite fruit and quantity.

    :param user_name: Name of the user.
    :param fruit: The preferred fruit.
    :param quantity: The quantity preferred (1, 2, or 3).
    :return: A descriptive string.
    """
    return f"{user_name} likes {quantity} {fruit.value}(s)."

print(favorite_fruit.schema())
```

## Documentation

### Parameter Types

- `str`: For string values.
- `int`: For integer values.
- `float`: For floating-point values.
- `typing.Literal`: For specifying a literal set of values.
- `Enum`: For enumerated types, with string values as Enum members.

### Decorator

- `@gptfunction`: This decorator should be used above the function definition. It processes the function and creates a GPT function schema.

### Methods

- `schema(use_required: bool)`: Returns the JSON schema of the wrapped function.
    - use_required: Indicates whether the schema should specify required parameters (default: True).
- `description()`: Retrieves the function's description from its docstring.
- `name()`: Returns the name of the function.

## Contributing

Contributions to improve `GPTFunction` are welcome. Please follow the standard procedures for submitting issues and pull requests on the project's GitHub repository.

## License

Distributed under the MIT License. See `LICENSE` for more information.
