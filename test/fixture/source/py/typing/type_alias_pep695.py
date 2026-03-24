from pytra.utils.assertions import py_assert_all, py_assert_eq, py_assert_true

type Scalar = int | float


def add_scalars(a: Scalar, b: Scalar) -> int:
    if isinstance(a, int) and isinstance(b, int):
        return a + b
    return 0


def identity_scalar(v: Scalar) -> Scalar:
    return v


def run_type_alias_pep695() -> bool:
    checks: list[bool] = []
    checks.append(py_assert_eq(add_scalars(1, 2), 3, "int+int"))
    checks.append(py_assert_eq(add_scalars(3, 4), 7, "int+int 2"))
    return py_assert_all(checks, "type_alias_pep695")


if __name__ == "__main__":
    print(run_type_alias_pep695())
