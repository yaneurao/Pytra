// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/argparse.py
// generated-by: tools/gen_runtime_from_manifest.py

const { PYTRA_TYPE_ID, PY_TYPE_MAP, PY_TYPE_OBJECT, pyRegisterClassType, pyBool, pyLen } = require("../../native/built_in/py_runtime.js");
const sys = require("./sys.js");

class Namespace {
    static PYTRA_TYPE_ID = pyRegisterClassType([PY_TYPE_OBJECT]);
    
    constructor(values) {
        if (values === null) {
            this.values = ({[PYTRA_TYPE_ID]: PY_TYPE_MAP});
            return;
        }
        this.values = values;
    this[PYTRA_TYPE_ID] = Namespace.PYTRA_TYPE_ID;
    }
}

class _ArgSpec {
    static PYTRA_TYPE_ID = pyRegisterClassType([PY_TYPE_OBJECT]);
    
    constructor(names, action, choices, py_default, help_text) {
        this.names = names;
        this.action = action;
        this.choices = choices;
        this.py_default = py_default;
        this.help_text = help_text;
        this.is_optional = (names).length > 0 && names[(((0) < 0) ? ((names).length + (0)) : (0))].startswith("-");
        if (this.is_optional) {
            let base = names[(((-1) < 0) ? ((names).length + (-1)) : (-1))].lstrip("-").replace("-", "_");
            this.dest = base;
        } else {
            this.dest = names[(((0) < 0) ? ((names).length + (0)) : (0))];
        }
    this[PYTRA_TYPE_ID] = _ArgSpec.PYTRA_TYPE_ID;
    }
}

class ArgumentParser {
    static PYTRA_TYPE_ID = pyRegisterClassType([PY_TYPE_OBJECT]);
    
    constructor(description) {
        this.description = description;
        this._specs = [];
    this[PYTRA_TYPE_ID] = ArgumentParser.PYTRA_TYPE_ID;
    }
    
    add_argument(name0, name1, name2, name3, help, action, choices, py_default) {
        let names = [];
        if (name0 !== "") {
            names.push(name0);
        }
        if (name1 !== "") {
            names.push(name1);
        }
        if (name2 !== "") {
            names.push(name2);
        }
        if (name3 !== "") {
            names.push(name3);
        }
        if ((names).length === 0) {
            throw new Error("add_argument requires at least one name");
        }
        let spec = new _ArgSpec(names, action, choices, py_default, help);
        this._specs.push(spec);
    }
    
    _fail(msg) {
        if (msg !== "") {
            sys.write_stderr(("error: " + String(msg) + "\n"));
        }
        throw SystemExit(2);
    }
    
    parse_args(argv) {
        let args;
        if (argv === null) {
            args = sys.argv.slice(1);
        } else {
            args = list(argv);
        }
        let specs_pos = [];
        let specs_opt = [];
        for (const s of this._specs) {
            if (s.is_optional) {
                specs_opt.push(s);
            } else {
                specs_pos.push(s);
            }
        }
        let by_name = ({[PYTRA_TYPE_ID]: PY_TYPE_MAP});
        let spec_i = 0;
        for (const s of specs_opt) {
            for (const n of s.names) {
                by_name[n] = spec_i;
            }
            spec_i += 1;
        }
        let values = ({[PYTRA_TYPE_ID]: PY_TYPE_MAP});
        for (const s of this._specs) {
            if (s.action === "store_true") {
                values[s.dest] = (s.py_default !== null ? pyBool(s.py_default) : false);
            } else {
                if (s.py_default !== null) {
                    values[s.dest] = s.py_default;
                } else {
                    values[s.dest] = null;
                }
            }
        }
        let pos_i = 0;
        let i = 0;
        while (i < (args).length) {
            let tok = args[(((i) < 0) ? ((args).length + (i)) : (i))];
            if (tok.startswith("-")) {
                if (!(Object.prototype.hasOwnProperty.call(by_name, tok))) {
                    this._fail(("unknown option: " + String(tok)));
                }
                let spec = specs_opt[(((by_name[tok]) < 0) ? ((specs_opt).length + (by_name[tok])) : (by_name[tok]))];
                if (spec.action === "store_true") {
                    values[spec.dest] = true;
                    i += 1;
                    continue;
                }
                if (i + 1 >= (args).length) {
                    this._fail(("missing value for option: " + String(tok)));
                }
                let val = args[(((i + 1) < 0) ? ((args).length + (i + 1)) : (i + 1))];
                if (pyLen(spec.choices) > 0 && !((val in spec.choices))) {
                    this._fail(("invalid choice for " + String(tok) + ": " + String(val)));
                }
                values[spec.dest] = val;
                i += 2;
                continue;
            }
            if (pos_i >= (specs_pos).length) {
                this._fail(("unexpected extra argument: " + String(tok)));
            }
            let spec = specs_pos[(((pos_i) < 0) ? ((specs_pos).length + (pos_i)) : (pos_i))];
            values[spec.dest] = tok;
            pos_i += 1;
            i += 1;
        }
        if (pos_i < (specs_pos).length) {
            this._fail(("missing required argument: " + String(specs_pos[(((pos_i) < 0) ? ((specs_pos).length + (pos_i)) : (pos_i))].dest)));
        }
        return values;
    }
}
