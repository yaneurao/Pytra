"""for loop over inline list of same-typed elements.

Verifies that EAST resolves the loop variable type from the element type
of a small inline list literal (e.g. [a, b] where a, b are str).
"""


from pytra.utils.assertions import py_assert_stdout


def find_optional(a: str, b: str) -> str:
    result: str = ""
    for candidate in [a, b]:
        if candidate.endswith(" | None"):
            result = candidate[:-7].strip()
    return result


def join_list() -> str:
    result: str = ""
    for x in ["hello", "world"]:
        if result != "":
            result = result + ","
        result = result + x
    return result


def sum_list() -> int:
    total: int = 0
    for n in [10, 20, 30]:
        total = total + n
    return total


def _case_main() -> None:
    print(find_optional("foo | None", "bar"))
    print(join_list())
    print(sum_list())


if __name__ == "__main__":
    print(py_assert_stdout(["foo", "hello,world", "60"], _case_main))
