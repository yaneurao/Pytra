from pylib.std import json
from pylib.tra.assertions import py_assert_stdout


def main() -> None:
    obj = json.loads('{"a":1,"b":[true,false,null],"s":"\\u3042"}')
    print(obj["a"])
    print(obj["b"][1])
    print(obj["b"][2] is None)
    print(obj["s"])

    escaped = json.loads('{"t":"a\\\\b\\n\\t\\\"\\/"}')
    print(escaped["t"] == 'a\\b\n\t"/')

    compact = json.dumps({"x": [1, 2], "s": "あ"}, ensure_ascii=True, separators=(",", ":"))
    print("\\u3042" in compact)
    print('"x":[1,2]' in compact)

    pretty = json.dumps({"k": 1}, ensure_ascii=False, indent=2)
    print("\n" in pretty)
    print('  "k"' in pretty)

    try:
        json.loads('{"a":1')
        print("NoError")
    except ValueError:
        print("ValueError")


def _case_main() -> None:
    main()


if __name__ == "__main__":
    print(
        py_assert_stdout(
            ["1", "False", "True", "あ", "True", "True", "True", "True", "True", "ValueError"],
            _case_main,
        )
    )
