import pytest
from pipes import Pipe

# --- Fixtures (Setup) ---
# We define simple math functions to make assertions easy


@Pipe
def add_five(x):
    return x + 5


@Pipe
def double(x):
    return x * 2


@Pipe
def stringify(x):
    return str(x)

# --- Tests ---


def test_basic_piping_execution():
    """Test: 10 | add_five"""
    result = 10 | add_five
    assert result == 15


def test_chained_execution_order():
    """Test: 10 | add_five | double"""
    # Should be (10 + 5) * 2 = 30
    # If order was wrong (10 * 2) + 5 = 25
    result = 10 | add_five | double
    assert result == 30


def test_pipeline_creation_composition():
    """Test: chain = add_five | double"""
    chain = add_five | double

    # It should return a Pipe object, not a result yet
    assert isinstance(chain, Pipe)

    # Now execute
    assert chain(10) == 30


def test_inplace_function_chaining():
    """Test: func |= other_func"""
    # We need a fresh copy or a local function so we don't pollute the global fixture
    @Pipe
    def start(x): return x + 1

    @Pipe
    def end(x): return x * 10

    # Mutate 'start' to include 'end'
    start |= end

    # (2 + 1) * 10 = 30
    assert start(2) == 30


def test_variable_inplace_pipe():
    """
    Test: variable |= func
    """
    val = 10

    # Equivalent to: val = val | add_five
    # 10 | add_five -> 15 -> val becomes 15
    val |= add_five

    assert val == 15

    # Chain it: 15 | double -> 30
    val |= double
    assert val == 30


def test_variable_inplace_pipe_chain():
    """
    Test: variable |= add_five | double
    """
    val = 10

    val |= add_five | double

    assert val == 30

# --- Multiple Arguments ---


@Pipe
def add_numbers(a, b):
    return a + b


@Pipe
def double_numbers(a, b):
    return a * 2, b * 2


@Pipe
def my_pow(*, a=0, b=0):
    return a ** b


def test_multi_arg_piping_execution():
    """Test: (3, 4) | add_numbers"""
    result = (3, 4) | add_numbers
    assert result == 7


def test_multi_arg_execution_order():
    """Test: (3, 4) | double_numbers | add_numbers"""
    # Should be (3 * 2 + 4 * 2) = 14
    result = (3, 4) | double_numbers | add_numbers
    assert result == 14


def test_multi_kwarg_piping_execution():
    """Test: {a: 2, b: 3} | raise"""
    result = {'a': 2, 'b': 3} | my_pow
    assert result == 8


# --- Set & Dict ---

@Pipe
def count_items(data):
    return len(data)


def test_list_works():
    """
    Test: list | func
    Native behavior: [1,2,3] | func -> 3.
    """
    nums = [1, 2, 3]

    res = nums | count_items

    assert res == 3


def test_set_works():
    """
    Test: set | func
    Native behavior: {1,2} | func -> TypeError.
    Solution: Box({1,2}) | func
    """
    nums = {1, 2, 3}

    res = nums | count_items

    assert res == 3


# --- Broadcast ---

@Pipe(broadcast=True)
def double(x):
    return x * 2


def test_broadcast():
    data = [1, 2, 3, 4, 5]

    res = data | double

    assert res == [2, 4, 6, 8, 10]


def test_pipe_to_normal_function():
    data = [1, 2, 3, 4, 5]

    res = data | (double | sum)

    assert res == 30
