from pytra.utils.assertions import py_assert_stdout
from pytra.std.json import JsonVal


def make_nullable_span(has_value: bool) -> dict[str, JsonVal]:
    d: dict[str, JsonVal] = {}
    if has_value:
        d["lineno"] = 1
        d["col"] = 0
    return d


def describe_span(span: dict[str, JsonVal]) -> str:
    lineno: JsonVal = span.get("lineno", None)
    if lineno is None:
        return "empty"
    return "line=" + str(lineno)


def _case_main() -> None:
    full: dict[str, JsonVal] = make_nullable_span(True)
    empty: dict[str, JsonVal] = make_nullable_span(False)
    print(describe_span(full))
    print(describe_span(empty))


if __name__ == "__main__":
    print(py_assert_stdout(["line=1", "empty"], _case_main))
