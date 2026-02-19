from pylib.std import json
from pylib.tra.assertions import py_assert_all, py_assert_eq


def run_json_extended() -> bool:
    checks: list[bool] = []
    obj = json.loads('{"a":1,"b":[true,false,null],"s":"\\u3042"}')
    checks.append(py_assert_eq(obj["a"], 1, "obj.a"))
    checks.append(py_assert_eq(obj["b"][1], False, "obj.b[1]"))
    checks.append(py_assert_eq(obj["b"][2] is None, True, "obj.b[2] is None"))
    checks.append(py_assert_eq(obj["s"], "あ", "obj.s"))

    escaped = json.loads('{"t":"a\\\\b\\n\\t\\\"\\/"}')
    checks.append(py_assert_eq(escaped["t"] == 'a\\b\n\t"/', True, "escaped"))

    compact = json.dumps({"x": [1, 2], "s": "あ"}, ensure_ascii=True, separators=(",", ":"))
    checks.append(py_assert_eq("\\u3042" in compact, True, "compact-unicode"))
    checks.append(py_assert_eq('"x":[1,2]' in compact, True, "compact-array"))

    pretty = json.dumps({"k": 1}, ensure_ascii=False, indent=2)
    checks.append(py_assert_eq("\n" in pretty, True, "pretty-newline"))
    checks.append(py_assert_eq('  "k"' in pretty, True, "pretty-indent"))

    try:
        json.loads('{"a":1')
        checks.append(py_assert_eq("NoError", "ValueError", "invalid-json"))
    except ValueError:
        checks.append(py_assert_eq("ValueError", "ValueError", "invalid-json"))
    return py_assert_all(checks, "json_extended")


if __name__ == "__main__":
    print(run_json_extended())
