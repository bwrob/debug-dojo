"""Test the compare utilities."""

from rich.text import Text

from debug_dojo._compare import (
    get_object_attributes,
    get_object_methods,
    get_simplified_object_info,
)


def test_get_object_attributes() -> None:
    """Test that object attributes are correctly extracted."""

    class MyClass:
        """A simple class for testing."""

        x: int = 10
        y: str = "hello"

        def my_method(self) -> None:
            """Do something."""

    obj = MyClass()
    attributes = get_object_attributes(obj)
    assert "x=10" in attributes
    assert "y='hello'" in attributes
    assert "my_method" not in attributes


def test_get_object_methods() -> None:
    """Test that object methods are correctly extracted."""

    class MyClass:
        """A simple class for testing."""

        x: int = 10

        def my_method(self) -> None:
            """Do something."""

        def _private_method(self) -> None:
            """Do something else."""

    obj = MyClass()
    methods = get_object_methods(obj)
    assert "my_method" in methods
    assert "_private_method" not in methods


def test_get_simplified_object_info_basic_type() -> None:
    """Test simplified object info for basic types."""
    info = get_simplified_object_info(123)
    assert any(isinstance(line, Text) and "123" in line.plain for line in info)


def test_get_simplified_object_info_custom_object() -> None:
    """Test simplified object info for custom objects."""

    class MyClass:
        """A simple class for testing."""

        x: int = 10

        def my_method(self) -> None:
            """Do something."""

    obj = MyClass()
    info = get_simplified_object_info(obj)

    # Check that basic info is present
    assert any(isinstance(line, Text) and "MyClass" in line.plain for line in info)
    assert any(isinstance(line, Text) and "x=10" in line.plain for line in info)
    assert any(isinstance(line, Text) and "my_method" in line.plain for line in info)
