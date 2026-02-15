def maybe_fail_69(flag: bool) -> int:
    try:
        if flag:
            raise Exception("fail-69")
        return 10
    except Exception as ex:
        return 20
    finally:
        pass


if __name__ == "__main__":
    print(maybe_fail_69(True))
