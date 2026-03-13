# This file contains test/implementation code for `test/fixtures/typing/property_method_call.py`.

from pytra.utils.assertions import py_assert_all, py_assert_eq


class MapperHolder:
    def __init__(self, mapper_value: int) -> None:
        self._mapper_value = mapper_value

    @property
    def mapper(self) -> int:
        return self._mapper_value

    def is_mmc3(self) -> bool:
        return self.mapper == 4

    def mapper_text(self) -> str:
        return str(self.mapper)


def run_property_method_call() -> bool:
    holder: MapperHolder = MapperHolder(4)
    checks: list[bool] = []
    checks.append(py_assert_eq(holder.mapper, 4, "property read"))
    checks.append(py_assert_eq(holder.is_mmc3(), True, "property compare"))
    checks.append(py_assert_eq(holder.mapper_text(), "4", "property stringify"))
    return py_assert_all(checks, "property_method_call")


if __name__ == "__main__":
    print(run_property_method_call())
