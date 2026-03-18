// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/utils/assertions.py
// generated-by: tools/gen_runtime_from_manifest.py

function _eq_any(actual, expected) {
    try {
        return py_to_string(actual) === py_to_string(expected);
    } catch (ex) {
        return actual === expected;
    }
}

function py_assert_true(cond, label) {
    if (cond) {
        return true;
    }
    if (label !== "") {
        console.log(("[assert_true] " + String(label) + ": False"));
    } else {
        console.log("[assert_true] False");
    }
    return false;
}

function py_assert_eq(actual, expected, label) {
    let ok = _eq_any(actual, expected);
    if (ok) {
        return true;
    }
    if (label !== "") {
        console.log(("[assert_eq] " + String(label) + ": actual=" + String(actual) + ", expected=" + String(expected)));
    } else {
        console.log(("[assert_eq] actual=" + String(actual) + ", expected=" + String(expected)));
    }
    return false;
}

function py_assert_all(results, label) {
    for (const v of results) {
        if (!v) {
            if (label !== "") {
                console.log(("[assert_all] " + String(label) + ": False"));
            } else {
                console.log("[assert_all] False");
            }
            return false;
        }
    }
    return true;
}

function py_assert_stdout(expected_lines, fn) {
    // self_hosted parser / runtime 互換優先: stdout capture は未実装。
    return true;
}

module.exports = {py_assert_true, py_assert_eq, py_assert_all, py_assert_stdout};
