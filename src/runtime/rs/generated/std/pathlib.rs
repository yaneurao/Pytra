// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/pathlib.py
// generated-by: tools/gen_runtime_from_manifest.py

mod py_runtime;
pub use crate::py_runtime::{math, pytra, time};
use crate::py_runtime::*;

use crate::pytra::std::glob as py_glob;
use crate::pytra::std::os;
use crate::pytra::std::os_path as path;

#[derive(Clone, Debug)]
struct Path {
    _value: String,
}
impl Path {
    fn new(value: String) -> Self {
        Self {
            _value: value,
        }
    }
    
    fn __str__(&self) -> String {
        return self._value;
    }
    
    fn __repr__(&self) -> String {
        return format!("{}{}{}", ("Path(").to_string(), self._value, (")").to_string());
    }
    
    fn __fspath__(&self) -> String {
        return self._value;
    }
    
    fn __truediv__(&self, rhs: &str) -> Path {
        return Path::new(((pytra::std::os_path::join(self._value, rhs)).to_string()));
    }
    
    fn parent(&self) -> Path {
        let mut parent_txt = pytra::std::os_path::dirname(self._value);
        if parent_txt == "" {
            parent_txt = (".").to_string();
        }
        return Path::new(((parent_txt).to_string()));
    }
    
    fn parents(&self) -> Vec<Path> {
        let mut out: Vec<Path> = vec![];
        let mut current: String = ((py_any_to_string(&pytra::std::os_path::dirname(self._value))).to_string());
        while true {
            if current == "" {
                current = (".").to_string();
            }
            out.push(Path::new(((current).to_string())));
            let mut next_current: String = ((py_any_to_string(&pytra::std::os_path::dirname(current))).to_string());
            if next_current == "" {
                next_current = (".").to_string();
            }
            if next_current == current {
                break;
            }
            current = next_current;
        }
        return out;
    }
    
    fn name(&self) -> String {
        return pytra::std::os_path::basename(self._value);
    }
    
    fn suffix(&self) -> String {
        let __tmp_1 = pytra::std::os_path::splitext(pytra::std::os_path::basename(self._value));
        let py_underscore = __tmp_1.0;
        let ext = __tmp_1.1;
        return ext;
    }
    
    fn stem(&self) -> String {
        let __tmp_2 = pytra::std::os_path::splitext(pytra::std::os_path::basename(self._value));
        let root = __tmp_2.0;
        let py_underscore = __tmp_2.1;
        return root;
    }
    
    fn resolve(&self) -> Path {
        return Path::new(((pytra::std::os_path::abspath(self._value)).to_string()));
    }
    
    fn exists(&self) -> bool {
        return pytra::std::os_path::exists(self._value);
    }
    
    fn mkdir(&self, parents: bool, exist_ok: bool) {
        if parents {
            pytra::std::os::makedirs(self._value, exist_ok);
            return;
        }
        if exist_ok && pytra::std::os_path::exists(self._value) {
            return;
        }
        pytra::std::os::mkdir(self._value);
    }
    
    fn read_text(&self, encoding: &str) -> String {
        let f = open(self._value, ("r").to_string(), encoding);
        {
            return f.read();
        }
        {
            f.close();
        }
    }
    
    fn write_text(&self, text: &str, encoding: &str) -> i64 {
        let f = open(self._value, ("w").to_string(), encoding);
        {
            return f.write(text);
        }
        {
            f.close();
        }
    }
    
    fn glob(&self, pattern: &str) -> Vec<Path> {
        let paths: Vec<String> = pytra::std::glob::glob(pytra::std::os_path::join(self._value, pattern));
        let mut out: Vec<Path> = vec![];
        for p in (paths).iter().cloned() {
            out.push(Path::new(((p).to_string())));
        }
        return out;
    }
    
    fn cwd() -> Path {
        return Path::new(((pytra::std::os::getcwd()).to_string()));
    }
}


fn main() {
    ("Pure Python Path helper compatible with a subset of pathlib.Path.").to_string();
}
