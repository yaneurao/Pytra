// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/pathlib.py
// generated-by: tools/gen_runtime_from_manifest.py

using System;
using System.Collections.Generic;
using System.Linq;
using Any = System.Object;
using int64 = System.Int64;
using float64 = System.Double;
using str = System.String;
using Pytra.CsModule;
using py_glob = Pytra.CsModule;
using path = Pytra.CsModule;

public class Path
{
    public static readonly long PYTRA_TYPE_ID = Pytra.CsModule.py_runtime.py_register_class_type(Pytra.CsModule.py_runtime.PYTRA_TID_OBJECT);
    public str _value;
    
    public Path(str value)
    {
        this._value = value;
    }
    
    public str __str__()
    {
        return this._value;
    }
    
    public str __repr__()
    {
        return "Path(" + this._value + ")";
    }
    
    public str __fspath__()
    {
        return this._value;
    }
    
    public Path __truediv__(str rhs)
    {
        return new Path(path.join(this._value, rhs));
    }
    
    public Path parent()
    {
        var parent_txt = path.dirname(this._value);
        if ((parent_txt) == ("")) {
            parent_txt = ".";
        }
        return new Path(parent_txt);
    }
    
    public System.Collections.Generic.List<Path> parents()
    {
        System.Collections.Generic.List<Path> py_out = new System.Collections.Generic.List<Path>();
        str current = System.Convert.ToString(path.dirname(this._value));
        while (true) {
            if ((current) == ("")) {
                current = ".";
            }
            py_out.Add(new Path(current));
            str next_current = System.Convert.ToString(path.dirname(current));
            if ((next_current) == ("")) {
                next_current = ".";
            }
            if ((next_current) == (current)) {
                break;
            }
            current = next_current;
        }
        return py_out;
    }
    
    public str name()
    {
        return path.basename(this._value);
    }
    
    public str suffix()
    {
        var __tmp_1 = path.splitext(path.basename(this._value));
        var _ = __tmp_1.Item1;
        var ext = __tmp_1.Item2;
        return ext;
    }
    
    public str stem()
    {
        var __tmp_2 = path.splitext(path.basename(this._value));
        var root = __tmp_2.Item1;
        var _ = __tmp_2.Item2;
        return root;
    }
    
    public Path resolve()
    {
        return new Path(path.abspath(this._value));
    }
    
    public bool exists()
    {
        return path.exists(this._value);
    }
    
    public void mkdir(bool parents = false, bool exist_ok = false)
    {
        if (parents) {
            os.makedirs(this._value, exist_ok);
            return;
        }
        if ((exist_ok) && (path.exists(this._value))) {
            return;
        }
        os.mkdir(this._value);
    }
    
    public str read_text(str encoding = "utf-8")
    {
        PyFile f = Pytra.CsModule.py_runtime.open(this._value, "r");
        try
        {
            return f.read();
        } finally {
            f.close();
        }
    return default(str);
    }
    
    public int64 write_text(str text, str encoding = "utf-8")
    {
        PyFile f = Pytra.CsModule.py_runtime.open(this._value, "w");
        try
        {
            return f.write(text);
        } finally {
            f.close();
        }
    return default(int64);
    }
    
    public System.Collections.Generic.List<Path> glob(str pattern)
    {
        System.Collections.Generic.List<str> paths = py_glob.glob(path.join(this._value, pattern));
        System.Collections.Generic.List<Path> py_out = new System.Collections.Generic.List<Path>();
        foreach (var p in paths) {
            py_out.Add(new Path(p));
        }
        return py_out;
    }
    
    public static Path cwd()
    {
        return new Path(os.getcwd());
    }
}

public static class Program
{
    public static void Main(string[] args)
    {
    }
}
