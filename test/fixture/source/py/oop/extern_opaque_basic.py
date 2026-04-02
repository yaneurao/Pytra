from pytra.utils.assertions import py_assert_all, py_assert_eq, py_assert_true


@extern
class Handle:
    def get_id(self) -> int: ...
    def close(self) -> None: ...


@extern
class Factory:
    def create(self, name: str) -> Handle: ...
    def destroy(self, h: Handle) -> None: ...


def use_opaque(factory: Factory, name: str) -> int:
    h: Handle = factory.create(name)
    result: int = h.get_id()
    h.close()
    factory.destroy(h)
    return result


def opaque_in_list(factory: Factory) -> int:
    handles: list[Handle] = []
    i: int = 0
    while i < 3:
        handles.append(factory.create("h" + str(i)))
        i += 1
    total: int = 0
    for h in handles:
        total += h.get_id()
        h.close()
    return total


def opaque_optional(factory: Factory) -> bool:
    h: Handle | None = None
    if h is None:
        h = factory.create("test")
    result: int = h.get_id()
    h.close()
    return result >= 0


def opaque_equality(factory: Factory) -> bool:
    h1: Handle = factory.create("a")
    h2: Handle = factory.create("b")
    same: bool = h1 == h1
    diff: bool = h1 == h2
    h1.close()
    h2.close()
    return same and not diff
