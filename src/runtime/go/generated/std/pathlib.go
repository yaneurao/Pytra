// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/pathlib.py
// generated-by: tools/gen_runtime_from_manifest.py

package main

type PathLike interface {
    __str__() string
    __repr__() string
    __fspath__() string
    __truediv__(rhs string) *Path
    parent() *Path
    parents() []any
    name() string
    suffix() string
    stem() string
    resolve() *Path
    exists() bool
    mkdir(parents bool, exist_ok bool)
    read_text(encoding string) string
    write_text(text string, encoding string) int64
    glob(pattern string) []any
    cwd() *Path
}


func __pytra_is_Path(v any) bool {
    _, ok := v.(*Path)
    return ok
}

func __pytra_as_Path(v any) *Path {
    if t, ok := v.(*Path); ok {
        return t
    }
    return nil
}

type Path struct {
    _value string
}

func NewPath(value string) *Path {
    self := &Path{}
    self.Init(value)
    return self
}

func (self *Path) Init(value string) {
    self._value = value
}

func (self *Path) __str__() string {
    return __pytra_str(self._value)
}

func (self *Path) __repr__() string {
    return __pytra_str((__pytra_str((__pytra_str("Path(") + __pytra_str(self._value))) + __pytra_str(")")))
}

func (self *Path) __fspath__() string {
    return __pytra_str(self._value)
}

func (self *Path) __truediv__(rhs string) *Path {
    return __pytra_as_Path(NewPath(path.join(self._value, rhs)))
}

func (self *Path) parent() *Path {
    var parent_txt any = path.dirname(self._value)
    if (__pytra_str(parent_txt) == __pytra_str("")) {
        parent_txt = "."
    }
    return __pytra_as_Path(NewPath(parent_txt))
}

func (self *Path) parents() []any {
    var out []any = __pytra_as_list([]any{})
    var current string = __pytra_str(path.dirname(self._value))
    for true {
        if (__pytra_str(current) == __pytra_str("")) {
            current = __pytra_str(".")
        }
        out = append(out, NewPath(current))
        var next_current string = __pytra_str(path.dirname(current))
        if (__pytra_str(next_current) == __pytra_str("")) {
            next_current = __pytra_str(".")
        }
        if (__pytra_str(next_current) == __pytra_str(current)) {
            break
        }
        current = __pytra_str(next_current)
    }
    return __pytra_as_list(out)
}

func (self *Path) name() string {
    return __pytra_str(path.basename(self._value))
}

func (self *Path) suffix() string {
    __tuple_0 := __pytra_as_list(path.splitext(path.basename(self._value)))
    _ = __tuple_0[0]
    var ext any = __tuple_0[1]
    _ = ext
    return __pytra_str(ext)
}

func (self *Path) stem() string {
    __tuple_0 := __pytra_as_list(path.splitext(path.basename(self._value)))
    var root any = __tuple_0[0]
    _ = root
    _ = __tuple_0[1]
    return __pytra_str(root)
}

func (self *Path) resolve() *Path {
    return __pytra_as_Path(NewPath(path.abspath(self._value)))
}

func (self *Path) exists() bool {
    return __pytra_truthy(path.exists(self._value))
}

func (self *Path) mkdir(parents bool, exist_ok bool) {
    if parents {
        os.makedirs(self._value, exist_ok)
        return
    }
    if (exist_ok && __pytra_truthy(path.exists(self._value))) {
        return
    }
    os.mkdir(self._value)
}

func (self *Path) read_text(encoding string) string {
    f := open(self._value, "r", encoding)
    return __pytra_str(f.read())
    f.close()
    return ""
}

func (self *Path) write_text(text string, encoding string) int64 {
    f := open(self._value, "w", encoding)
    return __pytra_int(f.write(text))
    f.close()
    return 0
}

func (self *Path) glob(pattern string) []any {
    var paths []any = __pytra_as_list(py_glob.glob(path.join(self._value, pattern)))
    var out []any = __pytra_as_list([]any{})
    __iter_0 := __pytra_as_list(paths)
    for __i_1 := int64(0); __i_1 < int64(len(__iter_0)); __i_1 += 1 {
        var p string = __pytra_str(__iter_0[__i_1])
        out = append(out, NewPath(p))
    }
    return __pytra_as_list(out)
}

func (self *Path) cwd() *Path {
    return __pytra_as_Path(NewPath(os.getcwd()))
}
