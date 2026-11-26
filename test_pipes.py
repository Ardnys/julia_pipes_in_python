import importlib.util
import inspect
from functools import partial

import pytest

from paipu import Pipe, broadcast, splat


@Pipe
def add_five(x):
    return x + 5


@Pipe
def double(x):
    return x * 2


@Pipe
def count_items(data):
    return len(data)


@Pipe
def identity(x):
    return x


# --- Applying and composing ---


def test_basic_piping_execution():
    assert 10 | add_five == 15


def test_chained_execution_order():
    # (10 + 5) * 2 = 30; the wrong order would give (10 * 2) + 5 = 25
    assert 10 | add_five | double == 30


def test_pipeline_creation_composition():
    chain = add_five | double

    assert isinstance(chain, Pipe)
    assert chain(10) == 30


def test_grouping_does_not_matter():
    assert 10 | add_five | double == 10 | (add_five | double) == double(add_five(10))


def test_compose_with_plain_callable():
    assert 10 | (double | str) == "20"
    assert 10 | double | Pipe(str) == "20"


def test_composition_is_flat():
    chain = add_five | (double | count_items) | str
    assert len(chain._stages) == 4


def test_compose_with_non_callable_fails():
    with pytest.raises(TypeError):
        _ = add_five | 3  # pyright: ignore[reportOperatorIssue]


def test_pipe_rejects_non_callable():
    with pytest.raises(TypeError, match="callable"):
        Pipe(3)  # pyright: ignore[reportArgumentType]


def test_composed_call_forwards_all_arguments():
    @Pipe
    def add(a, b=0):
        return a + b

    assert (add | double)(1, b=2) == 6


# --- In-place |= ---


def test_inplace_function_chaining():
    @Pipe
    def start(x):
        return x + 1

    original = start
    start |= double

    assert start(2) == 6
    assert original(2) == 3  # composing creates a new pipe; the original is unchanged


def test_variable_inplace_pipe():
    val = 10
    val |= add_five
    assert val == 15
    val |= double
    assert val == 30


def test_variable_inplace_pipe_chain():
    val = 10
    val |= add_five | double
    assert val == 30


def test_set_inplace_pipe():
    val = {1, 2, 3}
    val |= count_items
    assert val == 3


# --- Containers are passed as a single value ---


@pytest.mark.parametrize("data", [[1, 2, 3], (1, 2, 3), {1, 2, 3}, {"a": 1, "b": 2, "c": 3}, "abc"])
def test_containers_are_not_spread(data):
    assert data | count_items == 3


def test_dict_or_pipe():
    # `dict | x` returns NotImplemented for non-dicts, so Pipe.__ror__ runs.
    assert {"a": 1} | count_items == 1


def test_none_and_types_are_values():
    assert None | Pipe(repr) == "None"
    assert int | Pipe(repr) == "<class 'int'>"


def test_plain_callable_on_left_is_a_value():
    assert len | Pipe(callable) is True


# --- splat ---


@Pipe
def add_numbers(a, b):
    return a + b


@Pipe
def double_numbers(a, b):
    return a * 2, b * 2


def my_pow(*, a=0, b=0):
    return a**b


def test_splat_tuple():
    assert (3, 4) | splat(add_numbers) == 7


def test_splat_in_chain():
    # (3 * 2 + 4 * 2) = 14
    assert (3, 4) | splat(double_numbers) | splat(add_numbers) == 14
    assert (3, 4) | (splat(double_numbers) | splat(add_numbers)) == 14


def test_splat_dict_to_kwargs():
    assert {"a": 2, "b": 3} | splat(my_pow) == 8


def test_splat_as_decorator():
    @splat
    def area(w, h):
        return w * h

    assert (2, 5) | area == 10
    assert area((2, 5)) == 10


# --- broadcast ---


def test_broadcast():
    assert [1, 2, 3, 4, 5] | broadcast(double) == [2, 4, 6, 8, 10]


def test_broadcast_composes_with_plain_function():
    # Element-wise doubling, then sum: 2 + 4 + 6 + 8 + 10 = 30.
    # (Without broadcasting, the list itself would be doubled and summed, also to 30.)
    assert [1, 2, 3, 4, 5] | (broadcast(double) | sum) == 30
    assert [1, 2] | (broadcast(double) | list) == [2, 4]


def test_broadcast_direct_call():
    assert broadcast(double)([1, 2]) == [2, 4]


def test_broadcast_generator():
    assert (x for x in range(3)) | broadcast(add_five) == [5, 6, 7]


def test_broadcast_treats_strings_and_scalars_as_scalars():
    assert "ab" | broadcast(double) == "abab"
    assert 3 | broadcast(double) == 6


def test_broadcast_splat():
    assert [(1, 2), (3, 4)] | broadcast(splat(add_numbers)) == [3, 7]


def test_broadcast_as_decorator():
    @broadcast
    def inc(x):
        return x + 1

    assert [1, 2] | inc == [2, 3]


# --- Metadata, methods, repr ---


def test_wraps_metadata():
    @Pipe
    def documented(x):
        """Docs."""
        return x

    assert documented.__name__ == "documented"
    assert documented.__doc__ == "Docs."
    assert str(inspect.signature(documented)) == "(x)"


def test_repr():
    assert repr(add_five) == "Pipe(add_five)"
    assert repr(add_five | double | str) == "Pipe(add_five | double | str)"
    assert repr(broadcast(splat(add_numbers))) == "Pipe(broadcast(splat(add_numbers)))"


def test_partial_has_a_name():
    p = Pipe(partial(pow, 2))
    assert 3 | p == 8
    assert "partial" in repr(p)


def test_pipe_of_pipe():
    assert Pipe(add_five)(1) == 6


def test_method_decorator():
    class Greeter:
        def __init__(self, greeting):
            self.greeting = greeting

        @Pipe
        def greet(self, name):
            return f"{self.greeting}, {name}"

    hello = Greeter("hello")

    assert "bob" | hello.greet == "hello, bob"
    assert hello.greet("bob") == "hello, bob"
    assert "bob" | (hello.greet | str.upper) == "HELLO, BOB"
    assert Greeter.greet(hello, "bob") == "hello, bob"


@pytest.mark.skipif(importlib.util.find_spec("numpy") is None, reason="numpy not installed")
def test_numpy_array_on_left():
    import numpy as np  # pyright: ignore[reportMissingImports]

    assert np.array([1, 2, 3]) | Pipe(np.sum) == 6


@pytest.mark.skipif(importlib.util.find_spec("pandas") is None, reason="pandas not installed")
def test_pandas_objects_on_left():
    import pandas as pd  # pyright: ignore[reportMissingImports]

    frame = pd.DataFrame({"a": [1, 2, 3]})

    assert frame | count_items == 3  # pyright: ignore[reportGeneralTypeIssues]  # see paipu docstring
    assert frame["a"] | Pipe(sum) == 6
    assert frame.index | count_items == 3
