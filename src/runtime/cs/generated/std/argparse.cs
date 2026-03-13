// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/argparse.py
// generated-by: tools/gen_runtime_from_manifest.py

using System;
using System.Collections.Generic;
using System.Linq;
using Any = System.Object;
using int64 = System.Int64;
using float64 = System.Double;
using str = System.String;
using Pytra.CsModule;

public class Namespace
{
    public static readonly long PYTRA_TYPE_ID = Pytra.CsModule.py_runtime.py_register_class_type(Pytra.CsModule.py_runtime.PYTRA_TID_OBJECT);
    public System.Collections.Generic.Dictionary<string, object> values;
    
    public Namespace(object values = null)
    {
        if ((values) == (null)) {
            this.values = new System.Collections.Generic.Dictionary<string, object>();
            return;
        }
        this.values = values;
    }
}

public class _ArgSpec
{
    public static readonly long PYTRA_TYPE_ID = Pytra.CsModule.py_runtime.py_register_class_type(Pytra.CsModule.py_runtime.PYTRA_TID_OBJECT);
    public System.Collections.Generic.List<string> names;
    public string action;
    public System.Collections.Generic.List<string> choices;
    public object py_default;
    public string help_text;
    public bool is_optional;
    public string dest;
    
    public _ArgSpec(System.Collections.Generic.List<string> names, string action, System.Collections.Generic.List<string> choices, object py_default = null, string help_text = "")
    {
        this.names = names;
        this.action = action;
        this.choices = choices;
        this.py_default = py_default;
        this.help_text = help_text;
        this.is_optional = ((((names).Count) > (0)) && (Pytra.CsModule.py_runtime.py_get(names, 0).StartsWith("-")));
        if (this.is_optional) {
            var py_base = Pytra.CsModule.py_runtime.py_get(names, -1).TrimStart(System.Convert.ToString("-").ToCharArray()).Replace("-", "_");
            this.dest = System.Convert.ToString(py_base);
        } else {
            this.dest = Pytra.CsModule.py_runtime.py_get(names, 0);
        }
    }
}

public class ArgumentParser
{
    public static readonly long PYTRA_TYPE_ID = Pytra.CsModule.py_runtime.py_register_class_type(Pytra.CsModule.py_runtime.PYTRA_TID_OBJECT);
    public string description;
    public System.Collections.Generic.List<_ArgSpec> _specs;
    
    public ArgumentParser(string description = "")
    {
        this.description = description;
        this._specs = new System.Collections.Generic.List<_ArgSpec>();
    }
    
    public void add_argument(string name0, string name1, string name2, string name3, string help, string action, System.Collections.Generic.List<string> choices, object py_default = null)
    {
        System.Collections.Generic.List<string> names = new System.Collections.Generic.List<string>();
        if ((name0) != ("")) {
            names.Add(name0);
        }
        if ((name1) != ("")) {
            names.Add(name1);
        }
        if ((name2) != ("")) {
            names.Add(name2);
        }
        if ((name3) != ("")) {
            names.Add(name3);
        }
        if (((names).Count) == (0)) {
            throw new System.Exception("add_argument requires at least one name");
        }
        _ArgSpec spec = new _ArgSpec(names, action, choices, py_default, help);
        this._specs.Add(spec);
    }
    
    public void _fail(string msg)
    {
        if ((msg) != ("")) {
            sys.write_stderr($"error: {msg}
");
        }
        throw SystemExit(2);
    }
    
    public System.Collections.Generic.Dictionary<string, object> parse_args(object argv = null)
    {
        System.Collections.Generic.List<string> args;
        if ((argv) == (null)) {
            args = args[System.Convert.ToInt32(null)];
        } else {
            args = new System.Collections.Generic.List<string>(argv);
        }
        System.Collections.Generic.List<_ArgSpec> specs_pos = new System.Collections.Generic.List<_ArgSpec>();
        System.Collections.Generic.List<_ArgSpec> specs_opt = new System.Collections.Generic.List<_ArgSpec>();
        foreach (var s in this._specs) {
            if (s.is_optional) {
                specs_opt.Add(s);
            } else {
                specs_pos.Add(s);
            }
        }
        System.Collections.Generic.Dictionary<string, long> by_name = new System.Collections.Generic.Dictionary<string, long>();
        long spec_i = 0;
        foreach (var s in specs_opt) {
            foreach (var n in ((System.Collections.IEnumerable)(s.names))) {
                by_name[n] = spec_i;
            }
            spec_i += 1;
        }
        System.Collections.Generic.Dictionary<string, object> values = new System.Collections.Generic.Dictionary<string, object>();
        foreach (var s in this._specs) {
            if ((s.action) == ("store_true")) {
                values[s.dest] = ((s.py_default) != (null) ? Pytra.CsModule.py_runtime.py_bool(s.py_default) : false);
            } else {
                if ((s.py_default) != (null)) {
                    values[s.dest] = s.py_default;
                } else {
                    values[s.dest] = null;
                }
            }
        }
        long pos_i = 0;
        long i = 0;
        while ((i) < ((args).Count)) {
            string tok = Pytra.CsModule.py_runtime.py_get(args, i);
            if (tok.StartsWith("-")) {
                if (!((by_name).ContainsKey(tok))) {
                    this._fail($"unknown option: {tok}");
                }
                _ArgSpec spec = Pytra.CsModule.py_runtime.py_get(specs_opt, by_name[tok]);
                if ((spec.action) == ("store_true")) {
                    values[spec.dest] = true;
                    i += 1;
                    continue;
                }
                if ((i + 1) >= ((args).Count)) {
                    this._fail($"missing value for option: {tok}");
                }
                string val = Pytra.CsModule.py_runtime.py_get(args, i + 1);
                if ((((spec.choices).Count()) > (0)) && (!((spec.choices).Contains(val)))) {
                    this._fail($"invalid choice for {tok}: {val}");
                }
                values[spec.dest] = val;
                i += 2;
                continue;
            }
            if ((pos_i) >= ((specs_pos).Count)) {
                this._fail($"unexpected extra argument: {tok}");
            }
            _ArgSpec spec = Pytra.CsModule.py_runtime.py_get(specs_pos, pos_i);
            values[spec.dest] = tok;
            pos_i += 1;
            i += 1;
        }
        if ((pos_i) < ((specs_pos).Count)) {
            this._fail($"missing required argument: {Pytra.CsModule.py_runtime.py_get(specs_pos, pos_i).dest}");
        }
        return values;
    }
}

public static class Program
{
    public static void Main(string[] args)
    {
    }
}
