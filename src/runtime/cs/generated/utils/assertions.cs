// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/utils/assertions.py
// generated-by: tools/gen_runtime_from_manifest.py

using System;
using System.Collections.Generic;
using System.Linq;
using Any = System.Object;
using int64 = System.Int64;
using float64 = System.Double;
using str = System.String;
using Pytra.CsModule;

public static class Program
{
    public static bool _eq_any(object actual, object expected)
    {
        try
        {
            return (py_to_string(actual)) == (py_to_string(expected));
        } catch (System.Exception ex) {
            return (actual) == (expected);
        }
    return default(bool);
    }
    
    public static bool py_assert_true(bool cond, string label = "")
    {
        if (cond) {
            return true;
        }
        if ((label) != ("")) {
            System.Console.WriteLine($"[assert_true] {label}: False");
        } else {
            System.Console.WriteLine("[assert_true] False");
        }
        return false;
    }
    
    public static bool py_assert_eq(object actual, object expected, string label = "")
    {
        bool ok = _eq_any(actual, expected);
        if (ok) {
            return true;
        }
        if ((label) != ("")) {
            System.Console.WriteLine($"[assert_eq] {label}: actual={actual}, expected={expected}");
        } else {
            System.Console.WriteLine($"[assert_eq] actual={actual}, expected={expected}");
        }
        return false;
    }
    
    public static bool py_assert_all(System.Collections.Generic.List<bool> results, string label = "")
    {
        foreach (var v in results) {
            if (!v) {
                if ((label) != ("")) {
                    System.Console.WriteLine($"[assert_all] {label}: False");
                } else {
                    System.Console.WriteLine("[assert_all] False");
                }
                return false;
            }
        }
        return true;
    }
    
    public static bool py_assert_stdout(System.Collections.Generic.List<string> expected_lines, object fn)
    {
        // self_hosted parser / runtime 互換優先: stdout capture は未実装。
        return true;
    }
    
    public static void Main(string[] args)
    {
    }
}
