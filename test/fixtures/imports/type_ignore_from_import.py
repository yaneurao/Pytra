from pytra.std.typing import Callable  # type:ignore


def takes_cb(cb: Callable) -> bool:
    return cb is not None


def main() -> None:
    print(takes_cb(main))


if __name__ == "__main__":
    main()
