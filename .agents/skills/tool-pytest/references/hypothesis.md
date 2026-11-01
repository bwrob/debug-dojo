# hypothesis Reference

`hypothesis` is an advanced property-based testing framework for Python. Instead
of testing hardcoded examples, `hypothesis` generates randomized inputs
to discover edge cases. It then automatically shrinks failing inputs to their
minimal reproducible form.

## 1. Core Syntax & Invariant Testing

Decorate test functions with `@given` and specify input generators from
`hypothesis.strategies`:

```python
from hypothesis import given
from hypothesis import strategies as st
from my_app.core import get_greeting


@given(st.text(min_size=1))
def test_greeting_always_contains_input(name: str):
    clean = name.strip()
    result = get_greeting(name)
    if clean:
        assert clean in result
    else:
        assert result == "Hello, World!"
```

## 2. Common Strategies

Hypothesis includes built-in strategies for primitive and composite data
types:

- **Primitives**: `st.integers(min_value=0, max_value=100)`, `st.booleans()`,
  `st.floats(allow_nan=False)`
- **Strings**: `st.text(alphabet=st.characters(whitelist_categories=("Lu", "Ll")))`
- **Collections**: `st.lists(st.integers(), min_size=1, max_size=50)`
- **Dictionaries**: `st.dictionaries(st.text(), st.integers())`
- **Dataclasses & Pydantic**: `st.builds(MyDataclass, field=st.integers())`

## 3. Shrinking and Reproducibility

When `hypothesis` encounters an assertion failure:

1. **Shrinking**: It prunes and simplifies failing inputs to isolate the
   exact trigger. For example, it reduces large strings to `""` or `" "`.
2. **Database Cache**: Hypothesis stores failing inputs in `.hypothesis/examples/`.
   Subsequent test runs re-test previously failing inputs first before exploring
   new random space.

## 4. Settings & Profiles

Customize test iterations, timeouts, and execution profiles:

### Local Test Tuning

```python
from hypothesis import given, settings
from hypothesis import strategies as st


@settings(max_examples=250, deadline=None)
@given(st.integers())
def test_compute(n: int):
    assert n + 0 == n
```

### Shared Profiles in `conftest.py`

Register standard execution profiles across the test suite:

```python
from hypothesis import HealthCheck, settings

settings.register_profile(
    "ci",
    max_examples=500,
    suppress_health_check=[HealthCheck.too_slow],
)
settings.register_profile("dev", max_examples=50)

# Load profile from environment variable or default to dev
settings.load_profile("dev")
```
