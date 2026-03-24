from pytra.utils.assertions import py_assert_stdout


def _case_main() -> None:
    # Basic numeric formatting
    fps: float = 29.97
    print(f"FPS {fps:5.1f}")

    # Integer formatting with width
    step: int = 42
    num_steps: int = 100
    loss: float = 0.0031
    print(f"step {step:4d} / {num_steps:4d} | loss {loss:.4f}")

    # Hex formatting
    value: int = 255
    print(f"hex={value:02x} HEX={value:02X}")

    # Comma grouping
    big: int = 1000000
    print(f"n={big:,d}")

    # Percent formatting
    ratio: float = 0.75
    print(f"ratio={ratio:.1%}")

    # Left-align string
    tag: str = "hi"
    print(f"[{tag:<6s}]")

    # Right-align integer with zero-fill
    code: int = 42
    print(f"code={code:06d}")

    # Sign display
    pos: int = 7
    neg: int = -3
    print(f"{pos:+d} {neg:+d}")


if __name__ == "__main__":
    expected: list[str] = [
        "FPS  30.0",
        "step   42 /  100 | loss 0.0031",
        "hex=ff HEX=FF",
        "n=1,000,000",
        "ratio=75.0%",
        "[hi    ]",
        "code=000042",
        "+7 -3",
    ]
    print(py_assert_stdout(expected, _case_main))
