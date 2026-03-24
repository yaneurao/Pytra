from pytra.std.pathlib import Path


def stringify(raw: object) -> str:
    path = Path(raw)
    return str(path)


def main() -> None:
    print(stringify("tmp/data.bin"))


if __name__ == "__main__":
    main()
