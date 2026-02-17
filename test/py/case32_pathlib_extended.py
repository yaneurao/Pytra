from pathlib import Path


def main() -> None:
    root = Path("test/obj/pathlib_case32")
    root.mkdir(parents=True, exist_ok=True)

    child = root / "values.txt"
    child.write_text("42")

    print(child.exists())
    print(child.name)
    print(child.stem)
    print((child.parent / "values.txt").exists())
    print(child.read_text())


if __name__ == "__main__":
    main()
