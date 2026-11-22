import logging
from functools import wraps

logger = logging.getLogger(__name__)


def main():
    @Pipe
    def foo(name: str) -> str:
        return name + "foo"

    name = "test"

    res = baz(bar(foo(name)))

    res1 = name | foo | bar | baz

    chain = foo | bar | baz
    res2 = chain(name)

    name |= foo | bar | baz

    foo |= bar | baz

    res3 = foo("test")

    print(res)
    print(res1)
    print(res2)
    print(res3)
    print(name)


class Pipe:
    def __init__(self, fn=None, broadcast=False):
        # broadcast
        if fn is None:
            self.fn = None
            self.broadcast = broadcast
            self.name = None
        else:
            self.fn = fn
            self.name = self.fn.__name__
            self.broadcast = broadcast
            wraps(fn)(self)
            logger.debug("registered function: %s", self.name)

    def __ror__(self, other):
        logger.debug("__ror__: %s other: %s - %s", self.name, other, type(other))
        if self.fn is None:
            raise NotImplementedError

        if self.broadcast:
            if hasattr(other, "__iter__") and not isinstance(other, (str, bytes)):
                return [self.fn(item) for item in other]

        # TODO: handle lists

        # spread args
        if isinstance(other, tuple):
            return self.fn(*other)

        # spread kwargs
        if isinstance(other, dict):
            return self.fn(**other)

        return self.fn(other)

    def __ior__(self, other):
        logger.debug(
            "__ior__ called for: %s with other: %s - %s",
            self.name,
            other,
            type(other),
        )
        return Pipe(lambda x: other(self.fn(x)))

    # this is not needed anymore
    def __or__(self, other):
        logger.debug("__or__: %s other: %s - %s", self.name, other, type(other))
        if isinstance(other, Pipe):
            return Pipe(lambda x: other(self.fn(x)))
        elif callable(other):
            return Pipe(lambda x: other(self.fn(x)))

        return NotImplemented

    # to call it like a function

    def __call__(self, *args, **kwargs):
        logger.debug("__call__ called for: %s with args: %s", self.name, args)
        # set up broadcast function
        if self.fn is None:
            fn = args[0]
            self.fn = fn
            return Pipe(self.fn, broadcast=self.broadcast)

        return self.fn(*args, **kwargs)


@Pipe
def bar(name: str) -> str:
    return f"__{name}__"


@Pipe
def baz(name: str) -> str:
    return f"☆{name}☆"


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format="%(levelname)s %(name)s: %(message)s")
    main()
