def maybe_fail_59(flag: bool) -> int:
    try:
        if flag:
            raise Exception("fail-59")
        return 10
    except Exception as ex:
        return 20
    finally:
        pass


if __name__ == "__main__":
    print(maybe_fail_59(True))
