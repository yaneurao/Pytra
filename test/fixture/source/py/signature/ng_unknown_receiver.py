# unknown receiver access test: method access on values with unresolved type
# (e.g. dict[str, Any].get() returning unknown) is rejected.
# This is a language constraint: all receivers must have a concrete type.

from pytra.typing import Any


def bad_unknown_receiver() -> int:
    table: dict[str, Any] = {"a": 1}
    val = table.get("a", 0)
    # val is inferred as 'unknown' because dict[str, Any].get() type is not resolved.
    # Attribute/method access on unknown-typed values must be rejected.
    return val.bit_length()


if __name__ == "__main__":
    print(bad_unknown_receiver())
