// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/sys.py
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
    public static void exit(long code = 0)
    {
        __s.exit(code);
    }
    
    public static void set_argv(System.Collections.Generic.List<string> values)
    {
        argv.clear();
        foreach (var v in values) {
            argv.append(v);
        }
    }
    
    public static void set_path(System.Collections.Generic.List<string> values)
    {
        path.clear();
        foreach (var v in values) {
            path.append(v);
        }
    }
    
    public static void write_stderr(string text)
    {
        __s.stderr.write(text);
    }
    
    public static void write_stdout(string text)
    {
        __s.stdout.write(text);
    }
    
    public static void Main(string[] args)
    {
            System.Collections.Generic.List<string> argv = py_extern(__s.argv);
            System.Collections.Generic.List<string> path = py_extern(__s.path);
            var stderr = py_extern(__s.stderr);
            var stdout = py_extern(__s.stdout);
    }
}
