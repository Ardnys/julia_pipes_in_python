"""Julia-style pipes for Python.

Decorate a function with ``@Pipe`` and it can be applied with ``|``::

    @Pipe
    def shout(s: str) -> str:
        return s.upper() + "!"

    "hi" | shout                     # -> "HI!"           (apply)
    loud = shout | str.strip         # -> Pipe            (compose)
    name = "hi" | shout | str.strip  # TypeError: see the caveats below
    name = "hi" | (shout | str.strip)
    name |= shout | str.strip        # name = name | (shout | str.strip)

Semantics are kept deliberately simple, mirroring Julia's ``|>``:

* ``value | f`` is always exactly ``f(value)``. Tuples and dicts are passed
  as a single argument. Use :func:`splat` to spread them into arguments.
* ``f | g`` composes left to right into a new :class:`Pipe`, so
  ``x | f | g == x | (f | g) == g(f(x))``.
* Calling a pipe directly, ``(f | g)(*args, **kwargs)``, passes the
  arguments to the first stage and the single result through the rest.

Caveats imposed by Python's operator dispatch:

* Applying needs a ``Pipe`` as the right operand. In ``x | f | str.upper``
  the second ``|`` sees two plain objects and fails. Write
  ``x | f | Pipe(str.upper)`` or ``x | (f | str.upper)`` instead.
* If the left operand is a ``Pipe``, ``|`` composes rather than applies.
  Any other callable on the left is treated as a value, like Julia's
  ``f |> g``.
* ``d |= pipe`` fails for a ``dict`` ``d``, because ``dict.__ior__``
  accepts any iterable and raises before ``Pipe`` gets a turn. Use
  ``d = d | pipe``. NumPy arrays and pandas objects have the same issue with
  in-place ``|=``.
* Static typing: pandas-stubs declare ``DataFrame.__or__`` as accepting
  anything, so type checkers infer ``frame | pipe`` as a ``DataFrame``.
  At runtime ``Pipe.__ror__`` handles it correctly.
"""

import logging
from collections.abc import Callable, Iterable, Mapping
from functools import update_wrapper
from types import MethodType
from typing import Any, Self, overload

__all__ = ["Pipe", "broadcast", "splat"]

logger = logging.getLogger(__name__)


def _name(fn: object) -> str:
    return getattr(fn, "__name__", None) or repr(fn)


class Pipe[**P, R]:
    """A callable that can be applied with ``value | pipe`` and composed with ``pipe | other``."""

    # Makes NumPy (and libraries following its protocol) return NotImplemented
    # from `array | pipe`, so Python falls back to `Pipe.__ror__`.
    __array_ufunc__ = None
    # Same for pandas: objects with a higher priority than DataFrame (4000)
    # make `frame | pipe` return NotImplemented.
    __pandas_priority__ = 5000

    _stages: tuple[Callable[..., Any], ...]

    def __init__(self, fn: Callable[P, R], /) -> None:
        if not callable(fn):
            raise TypeError(f"Pipe expects a callable, got {type(fn).__name__}")
        wrapped: Callable[..., Any] = fn
        update_wrapper(self, wrapped)
        if not hasattr(self, "__name__"):  # e.g. functools.partial
            self.__name__ = self.__qualname__ = repr(fn)
        # After update_wrapper: it copies `fn.__dict__`, which for a bound
        # method (see `__get__`) is the unbound pipe's, `_stages` included.
        self._stages = fn._stages if isinstance(fn, Pipe) else (fn,)

    @classmethod
    def _from_stages(cls, stages: tuple[Callable[..., Any], ...]) -> "Pipe[..., Any]":
        pipe = object.__new__(cls)
        pipe._stages = stages
        pipe.__name__ = pipe.__qualname__ = " | ".join(map(_name, stages))
        pipe.__doc__ = None
        return pipe

    def _run(self, *args: Any, **kwargs: Any) -> Any:
        first, *rest = self._stages
        result = first(*args, **kwargs)
        logger.debug("%s -> %r", _name(first), result)
        for stage in rest:
            result = stage(result)
            logger.debug("%s -> %r", _name(stage), result)
        return result

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R:
        return self._run(*args, **kwargs)

    def __ror__(self, value: Any) -> R:
        """``value | pipe``: apply the pipe to ``value``."""
        return self._run(value)

    def __or__[T](self, other: Callable[[R], T]) -> "Pipe[P, T]":
        """``pipe | other``: compose, running ``other`` on this pipe's result."""
        if not callable(other):
            return NotImplemented
        tail = other._stages if isinstance(other, Pipe) else (other,)
        return Pipe._from_stages(self._stages + tail)

    # `pipe |= other` falls back to `__or__`, rebinding the name to the composition.

    @overload
    def __get__(self, instance: None, owner: type | None = None) -> Self: ...
    @overload
    def __get__(self, instance: object, owner: type | None = None) -> "Pipe[..., R]": ...
    def __get__(self, instance: object | None, owner: type | None = None) -> "Pipe[..., Any]":
        """Bind like a function, so ``@Pipe`` also works on methods."""
        if instance is None:
            return self
        return Pipe(MethodType(self, instance))

    def __repr__(self) -> str:
        return f"Pipe({self.__name__})"


def broadcast[T, R](fn: Callable[[T], R], /) -> Pipe[[Iterable[T]], list[R]]:
    """Apply ``fn`` to each element, like Julia's ``.|>``.

    ``[1, 2, 3] | broadcast(f) == [f(1), f(2), f(3)]``. As in Julia, strings,
    bytes and non-iterables count as scalars, so ``f`` is applied to them
    directly.
    """

    apply: Callable[[Any], R] = fn

    def broadcasted(values: Any) -> Any:
        if isinstance(values, Iterable) and not isinstance(values, (str, bytes, bytearray)):
            return [apply(v) for v in values]
        return apply(values)

    broadcasted.__name__ = broadcasted.__qualname__ = f"broadcast({_name(fn)})"
    return Pipe(broadcasted)


def splat[R](fn: Callable[..., R], /) -> Pipe[[Iterable[Any] | Mapping[str, Any]], R]:
    """Spread the input into arguments, like Julia's ``splat``.

    ``(1, 2) | splat(f) == f(1, 2)`` and ``{"a": 1} | splat(f) == f(a=1)``.
    """

    def splatted(args: Iterable[Any] | Mapping[str, Any]) -> R:
        if isinstance(args, Mapping):
            return fn(**args)
        return fn(*args)

    splatted.__name__ = splatted.__qualname__ = f"splat({_name(fn)})"
    return Pipe(splatted)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format="%(levelname)s %(name)s: %(message)s")

    @Pipe
    def foo(name: str) -> str:
        return name + "foo"

    @Pipe
    def bar(name: str) -> str:
        return f"__{name}__"

    @Pipe
    def baz(name: str) -> str:
        return f"☆{name}☆"

    name = "test"
    assert name | foo | bar | baz == (foo | bar | baz)(name) == baz(bar(foo(name)))
    name |= foo | bar | baz
    print(name)
