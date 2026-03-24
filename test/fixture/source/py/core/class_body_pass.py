class Marker:
    pass


def main() -> None:
    m: Marker = Marker()
    print(m is not None)


if __name__ == "__main__":
    main()
