---
description: >-
  Engineering style guide for modern Python 3.12+ projects.
  Enforces PEP 695 generic syntax, structural protocols, frozen slots dataclasses, pure functional transformations, strict typing with Pyrefly, and composition over inheritance.
  Mandatory whenever writing, reviewing, architecting, refactoring, or type-checking Python code in this repository.
  Applies to source, tests, scripts, and hooks, even without prompt triggers.
  Triggers: python style, pep 695, protocols, dataclasses, typing, refactor.
name: guide-python
version: 1.1.0
---

# Modern Python 3.12+ Engineering Conventions (`guide-python`)

This style guide defines engineering standards for Python code in this
repository. It codifies Python 3.12+, PEP 695, structural
subtyping, functional transformation, and static typing.

---

## 1. Core Principles

1. **Explicit, Static Precision**: Every signature, return value, and interface
   boundary must have complete types. If you cannot express a type, refactor the design.
2. **Data & Behavior Separation**: Model data with immutable, transparent
   records (`dataclass(frozen=True)`). Express operations as pure functions.
3. **Composition over Inheritance**: Never use subclassing for code reuse. Compose
   objects or pass callable handlers.
4. **Structural over Nominal Subtyping**: Define consumption contracts using
   `typing.Protocol`. Depend on capabilities, not ancestry.
5. **Functional Transformations**: Prefer pure, idempotent functions without
   hidden side effects. Avoid in-place object mutation.
6. **Cognitive Simplicity**: Keep cyclomatic and cognitive complexity under 10
   (`complexipy`). Small, composable functions beat monolithic methods.

---

## 2. Python 3.12+ & PEP 695 Generics

Use native type parameter syntax and standard collection abstractions.

### Type Parameter Syntax

Do not use legacy `TypeVar`, `ParamSpec`, or `TypeAlias` imports. Use native
Python 3.12+ PEP 695 syntax:

```python
# ✅ CORRECT (PEP 695)
type JsonPrimitive = str | int | float | bool | None
type JsonValue = JsonPrimitive | list[JsonValue] | dict[str, JsonValue]
type Handler[T, R] = collections.abc.Callable[[T], R]


def first_or_default[T](items: collections.abc.Sequence[T], default: T) -> T:
    return items[0] if items else default


class Container[T]:
    def __init__(self, value: T) -> None:
        self.value = value
```

```python
# ❌ INCORRECT (Legacy TypeVar / TypeAlias)
from typing import TypeAlias, TypeVar

T = TypeVar("T")
JsonValue: TypeAlias = ...


def first_or_default(items: Sequence[T], default: T) -> T: ...
```

### Standard Generic Collections

Import collection abstract types from `collections.abc`, never from `typing`:

```python
# ✅ CORRECT
from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence


def process_batch(items: Sequence[str]) -> list[int]: ...
```

```python
# ❌ INCORRECT
from typing import Callable, Dict, List, Sequence
```

---

## 3. Data Modeling with Dataclasses

Model all domain entities with immutable, slotted dataclasses:

```python
from dataclasses import dataclass


@dataclass(frozen=True, slots=True, kw_only=True)
class UserProfile:
    user_id: str
    username: str
    email: str
    is_active: bool = True

    def __post_init__(self) -> None:
        if not self.email or "@" not in self.email:
            raise ValueError(f"Invalid email: {self.email}")
```

### Dataclass Guidelines

- Always set `frozen=True` and `slots=True`.
- Use `kw_only=True` when constructors have more than 2-3 fields to eliminate
  positional argument bugs.
- If data must change, use `dataclasses.replace` to produce a new instance.
  Do not mutate fields.

---

## 4. Structural Subtyping with Protocols

Define contracts based on what functions consume, not what classes implement:

```python
from typing import Protocol, runtime_checkable


@runtime_checkable
class DocumentReader(Protocol):
    def read(self, path: Path) -> str: ...


@runtime_checkable
class Serializer[T](Protocol):
    def serialize(self, item: T) -> bytes: ...
```

### Protocol Guidelines

- Keep protocols small (1-3 methods max). Follow the Interface Segregation
  Principle.
- Prefer callable protocols for single-method interfaces:

```python
class TokenProvider(Protocol):
    def __call__(self) -> str: ...
```

---

## 5. Composition Over Inheritance

Avoid class hierarchies. When you need polymorphism, use protocols,
callable injection, or algebraic sum types:

```python
# ✅ CORRECT: Composition via injected callable / protocol
@dataclass(frozen=True, slots=True)
class Pipeline:
    reader: DocumentReader
    filter_fn: Callable[[str], bool]

    def execute(self, path: Path) -> list[str]:
        content = self.reader.read(path)
        return [line for line in content.splitlines() if self.filter_fn(line)]
```

```python
# ❌ INCORRECT: Deep inheritance tree
class BasePipeline: ...


class FilteredPipeline(BasePipeline): ...


class S3FilteredPipeline(FilteredPipeline): ...
```

---

## 6. Functional Paradigm & Immutability

Design systems around deterministic data pipelines, immutability, and
structural matching.

### Pure Functions

Write functions that compute results purely from their arguments without
mutating inputs or holding external state:

```python
# ✅ CORRECT: Returns a new mapping, leaves input untouched
def inc_score(scores: Mapping[str, int], key: str, n: int) -> dict[str, int]:
    return {**scores, key: scores.get(key, 0) + n}
```

```python
# ❌ INCORRECT: In-place mutation of input dictionary
def inc_score(scores: dict[str, int], key: str, n: int) -> None:
    scores[key] = scores.get(key, 0) + n
```

### Pattern Matching

Use structural pattern matching (`match` / `case`) for message dispatch, sum
types, and AST transformations:

```python
type Action = (
    tuple[Literal["create"], str]
    | tuple[Literal["update"], str, dict[str, object]]
    | tuple[Literal["delete"], str]
)


def dispatch(action: Action) -> None:
    match action:
        case ("create", item_id):
            create_item(item_id)
        case ("update", item_id, payload):
            update_item(item_id, payload)
        case ("delete", item_id):
            delete_item(item_id)
        case _ as unreachable:
            if TYPE_CHECKING:
                assert_never(unreachable)
            logger.warning("Ignoring unknown action: %r", unreachable)
```

> [!TIP]
> **Forward-Compatible Exhaustiveness (`if TYPE_CHECKING: assert_never(...)`)**:
> For internal closed unions, call `typing.assert_never(x)` directly in the default branch.
> This makes both static type checkers and runtime fail on unhandled variants.
> External API payloads can add new enum values in the future without breaking existing clients.
> In that case, guard `assert_never(x)` behind `if TYPE_CHECKING:` and log a warning at runtime.

---

## 7. Strict Typing Guidelines

- **No `Any`**: Replace `Any` with `object` (if unconstrained), a generic type
  parameter `T`, or a precise union.
- **Explicit Returns**: Always declare return types, including `-> None`.
- **Narrow Types Early**: Use `assert`, `isinstance`, or `match` guards to narrow
  `object` or broad unions at system boundaries.
- **PEP 561**: Include `py.typed` in the package root.

---

## 8. Architectural Boundaries (Tach)

- **Strict Layering**: Follow module layer boundaries defined in `tach.toml`.
  - `cli` depends on `core`.
  - `core` NEVER imports from `cli`.
- **Zero Circular Imports**: Keep module dependencies as a Directed Acyclic
  Graph (DAG).

---

## 9. Docstrings & Markdown Rendering

- **NumPy-Style Markdown Docstrings**: Format public docstrings using the `numpy` convention
  (`Parameters`, `Returns`, `Raises`, `Examples`).
  Zensical and `mkdocstrings` render these docstrings as Markdown.
- **Single Backticks for Inline Code**: Docstrings parse as Markdown rather than
  reStructuredText (RST). Always use single backticks for inline code references
  (`` `value` ``), never RST double backticks (```` ``value`` ````).
- **Executable Doctests**: Include `>>>` doctest examples in pure functions when appropriate.
  Automated tests check these doctests via `pytest --doctest-modules`.

---

## 10. Terminal Output Conventions (Rich)

- **ASCII-Safe Glyphs**: Use plain ASCII status characters (`OK`, `PASS`,
  `[done]`) instead of decorative glyphs.
  Ruff rule `RUF001` flags lookalike glyphs such as the information sign
  (`U+2139`) in source code.
  ASCII output also survives byte-comparison in CI logs.
- **Byte-Stable Console Config**: Rich interim output must not depend on
  terminal width or locale:
  - `Console(highlight=False)` for deterministic plain text.
  - For passthrough of command output (linters, test runners), use
    `Console(markup=False, soft_wrap=True)`.
    This config stops Rich from interpreting bracket tags in tool output.
    It also stops Rich from rewrapping lines against a width guess.
- **No Width-Sensitive Formatting**: Avoid `Console.width`-sensitive
  formatting in CI assertions.
  Byte-compare only outputs produced with a pinned console config.
