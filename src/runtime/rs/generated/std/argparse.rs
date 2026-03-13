// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/argparse.py
// generated-by: tools/gen_runtime_from_manifest.py

mod py_runtime;
pub use crate::py_runtime::{math, pytra, time};
use crate::py_runtime::*;

use crate::pytra::std::sys;

#[derive(Clone, Debug)]
struct Namespace {
    values: ::std::collections::BTreeMap<String, PyAny>,
}
impl Namespace {
    fn new(values: PyAny) -> Self {
        Self {
            values: values,
        }
    }
}


#[derive(Clone, Debug)]
struct _ArgSpec {
    names: Vec<String>,
    action: String,
    choices: Vec<String>,
    default: PyAny,
    help_text: String,
    is_optional: bool,
    dest: String,
}
impl _ArgSpec {
    fn new(names: Vec<String>, action: String, choices: Vec<String>, default: PyAny, help_text: String) -> Self {
        Self {
            names: names,
            action: action,
            choices: choices,
            default: default,
            help_text: help_text,
            is_optional: ((names.len() as i64 > 0) && (names[((0) as usize)]).clone().startswith(("-").to_string())),
            dest: String::new(),
        }
    }
}


#[derive(Clone, Debug)]
struct ArgumentParser {
    description: String,
    _specs: Vec<_ArgSpec>,
}
impl ArgumentParser {
    fn new(description: String) -> Self {
        Self {
            description: description,
            _specs: vec![],
        }
    }
    
    fn add_argument(&mut self, name0: &str, name1: &str, name2: &str, name3: &str, help: &str, action: &str, choices: &[String], default: PyAny) {
        let mut names: Vec<String> = vec![];
        if name0 != "" {
            names.push(name0);
        }
        if name1 != "" {
            names.push(name1);
        }
        if name2 != "" {
            names.push(name2);
        }
        if name3 != "" {
            names.push(name3);
        }
        if names.len() as i64 == 0 {
            panic!("{}", ("add_argument requires at least one name").to_string());
        }
        let spec = _ArgSpec::new((names).clone(), action, choices, default, help);
        self._specs.push(spec);
    }
    
    fn _fail(&self, msg: &str) {
        if msg != "" {
            pytra::std::sys::write_stderr(f"error: {msg}\n");
        }
        panic!("{}", 2);
    }
    
    fn parse_args(&self, argv: PyAny) -> ::std::collections::BTreeMap<String, PyAny> {
        let mut args: Vec<String>;
        if argv == () {
            args = pytra::std::sys::argv[1..];
        } else {
            args = list(argv);
        }
        let mut specs_pos: Vec<_ArgSpec> = vec![];
        let mut specs_opt: Vec<_ArgSpec> = vec![];
        for s in (self._specs).iter() {
            if s.is_optional {
                specs_opt.push(s);
            } else {
                specs_pos.push(s);
            }
        }
        let mut by_name: ::std::collections::HashMap<String, i64> = ::std::collections::HashMap::from([]);
        let mut spec_i = 0;
        for s in (specs_opt).iter().cloned() {
            for n in s.names {
                by_name.insert(((n).to_string()), spec_i);
            }
            spec_i += 1;
        }
        let mut values: ::std::collections::HashMap<String, PyAny> = ::std::collections::HashMap::from([]);
        for s in (self._specs).iter() {
            if s.action == "store_true" {
                values.insert(((s.dest).to_string()), (if s.default != () { py_any_to_bool(&s.default) } else { false }));
            } else if s.default != () {
                values.insert(((s.dest).to_string()), s.default);
            } else {
                values.insert(((s.dest).to_string()), ());
            }
        }
        let mut pos_i = 0;
        let mut i = 0;
        while i < args.len() as i64 {
            let tok: &String = &(args[((i) as usize)]);
            if tok.startswith(("-").to_string()) {
                if !(by_name.contains_key(&tok)) {
                    self._fail(&(f"unknown option: {tok}"));
                }
                let mut spec = (specs_opt[((if ((by_name.get(&tok).cloned().expect("dict key not found")) as i64) < 0 { (specs_opt.len() as i64 + ((by_name.get(&tok).cloned().expect("dict key not found")) as i64)) } else { ((by_name.get(&tok).cloned().expect("dict key not found")) as i64) }) as usize)]).clone();
                if spec.action == "store_true" {
                    values.insert(((spec.dest).to_string()), true);
                    i += 1;
                    continue;
                }
                if i + 1 >= args.len() as i64 {
                    self._fail(&(f"missing value for option: {tok}"));
                }
                let val: &String = &(args[((if ((i + 1) as i64) < 0 { (args.len() as i64 + ((i + 1) as i64)) } else { ((i + 1) as i64) }) as usize)]);
                if (spec.choices.len() as i64 > 0) && (!(val == spec.choices)) {
                    self._fail(&(f"invalid choice for {tok}: {val}"));
                }
                values.insert(((spec.dest).to_string()), val);
                i += 2;
                continue;
            }
            if pos_i >= specs_pos.len() as i64 {
                self._fail(&(f"unexpected extra argument: {tok}"));
            }
            let mut spec = (specs_pos[((pos_i) as usize)]).clone();
            values.insert(((spec.dest).to_string()), tok);
            pos_i += 1;
            i += 1;
        }
        if pos_i < specs_pos.len() as i64 {
            self._fail(&(f"missing required argument: {specs_pos[pos_i].dest}"));
        }
        return values;
    }
}


fn main() {
    ("Minimal pure-Python argparse subset for selfhost usage.").to_string();
}
