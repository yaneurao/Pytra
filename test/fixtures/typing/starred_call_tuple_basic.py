from pytra.utils.assertions import py_assert_all


def mix_rgb(r: int, g: int, b: int) -> int:
    return (r << 16) | (g << 8) | b


def run_starred_call_tuple_basic() -> bool:
    rgb: tuple[int, int, int] = (1, 2, 3)
    packed: int = mix_rgb(*rgb)
    checks: list[bool] = [
        packed == 66051,
        mix_rgb(*rgb) == packed,
    ]
    return py_assert_all(checks, "starred_call_tuple_basic")


if __name__ == "__main__":
    print(run_starred_call_tuple_basic())
