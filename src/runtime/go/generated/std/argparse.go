// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/argparse.py
// generated-by: tools/gen_runtime_from_manifest.py

package main

type NamespaceLike interface {
}

type _ArgSpecLike interface {
}

type ArgumentParserLike interface {
    add_argument(name0 string, name1 string, name2 string, name3 string, help string, action string, choices []any, default_ any)
    _fail(msg string)
    parse_args(argv *Any) map[any]any
}


func __pytra_is_Namespace(v any) bool {
    _, ok := v.(*Namespace)
    return ok
}

func __pytra_as_Namespace(v any) *Namespace {
    if t, ok := v.(*Namespace); ok {
        return t
    }
    return nil
}

func __pytra_is__ArgSpec(v any) bool {
    _, ok := v.(*_ArgSpec)
    return ok
}

func __pytra_as__ArgSpec(v any) *_ArgSpec {
    if t, ok := v.(*_ArgSpec); ok {
        return t
    }
    return nil
}

func __pytra_is_ArgumentParser(v any) bool {
    _, ok := v.(*ArgumentParser)
    return ok
}

func __pytra_as_ArgumentParser(v any) *ArgumentParser {
    if t, ok := v.(*ArgumentParser); ok {
        return t
    }
    return nil
}

type Namespace struct {
    values map[any]any
}

func NewNamespace(values *Any) *Namespace {
    self := &Namespace{}
    self.Init(values)
    return self
}

func (self *Namespace) Init(values *Any) {
    if (values == nil) {
        self.values = map[any]any{}
        return
    }
    self.values = values
}

type _ArgSpec struct {
    names []any
    action string
    choices []any
    default_ *Any
    help_text string
    is_optional bool
    dest string
}

func New_ArgSpec(names []any, action string, choices []any, default_ any, help_text string) *_ArgSpec {
    self := &_ArgSpec{}
    self.Init(names, action, choices, default_, help_text)
    return self
}

func (self *_ArgSpec) Init(names []any, action string, choices []any, default_ any, help_text string) {
    self.names = names
    self.action = action
    self.choices = choices
    self.default_ = default_
    self.help_text = help_text
    self.is_optional = ((__pytra_len(names) > int64(0)) && __pytra_truthy(__pytra_str(__pytra_get_index(names, int64(0))).startswith("-")))
    if self.is_optional {
        var base any = __pytra_str(__pytra_get_index(names, (-int64(1)))).lstrip("-").replace("-", "_")
        self.dest = base
    } else {
        self.dest = __pytra_str(__pytra_get_index(names, int64(0)))
    }
}

type ArgumentParser struct {
    description string
    _specs []any
}

func NewArgumentParser(description string) *ArgumentParser {
    self := &ArgumentParser{}
    self.Init(description)
    return self
}

func (self *ArgumentParser) Init(description string) {
    self.description = description
    self._specs = []any{}
}

func (self *ArgumentParser) add_argument(name0 string, name1 string, name2 string, name3 string, help string, action string, choices []any, default_ any) {
    var names []any = __pytra_as_list([]any{})
    if (__pytra_str(name0) != __pytra_str("")) {
        names = append(names, name0)
    }
    if (__pytra_str(name1) != __pytra_str("")) {
        names = append(names, name1)
    }
    if (__pytra_str(name2) != __pytra_str("")) {
        names = append(names, name2)
    }
    if (__pytra_str(name3) != __pytra_str("")) {
        names = append(names, name3)
    }
    if (__pytra_len(names) == int64(0)) {
        panic(__pytra_str("add_argument requires at least one name"))
    }
    var spec *_ArgSpec = __pytra_as__ArgSpec(New_ArgSpec(names, action, choices, default_, help))
    self._specs = append(self._specs, spec)
}

func (self *ArgumentParser) _fail(msg string) {
    if (__pytra_str(msg) != __pytra_str("")) {
        sys.write_stderr(nil)
    }
    panic(__pytra_str(SystemExit(int64(2))))
}

func (self *ArgumentParser) parse_args(argv *Any) map[any]any {
    var args []any = nil
    if (argv == nil) {
        args = __pytra_as_list(__pytra_slice(sys.argv, int64(1), __pytra_len(sys.argv)))
    } else {
        args = __pytra_as_list(list(argv))
    }
    var specs_pos []any = __pytra_as_list([]any{})
    var specs_opt []any = __pytra_as_list([]any{})
    __iter_0 := __pytra_as_list(self._specs)
    for __i_1 := int64(0); __i_1 < int64(len(__iter_0)); __i_1 += 1 {
        var s *_ArgSpec = __pytra_as__ArgSpec(__iter_0[__i_1])
        if __pytra_truthy(s.is_optional) {
            specs_opt = append(specs_opt, s)
        } else {
            specs_pos = append(specs_pos, s)
        }
    }
    var by_name map[any]any = __pytra_as_dict(map[any]any{})
    var spec_i int64 = int64(0)
    __iter_2 := __pytra_as_list(specs_opt)
    for __i_3 := int64(0); __i_3 < int64(len(__iter_2)); __i_3 += 1 {
        var s *_ArgSpec = __pytra_as__ArgSpec(__iter_2[__i_3])
        __iter_4 := __pytra_as_list(s.names)
        for __i_5 := int64(0); __i_5 < int64(len(__iter_4)); __i_5 += 1 {
            n := __iter_4[__i_5]
            __pytra_set_index(by_name, n, spec_i)
        }
        spec_i += int64(1)
    }
    var values map[any]any = __pytra_as_dict(map[any]any{})
    __iter_6 := __pytra_as_list(self._specs)
    for __i_7 := int64(0); __i_7 < int64(len(__iter_6)); __i_7 += 1 {
        var s *_ArgSpec = __pytra_as__ArgSpec(__iter_6[__i_7])
        if (__pytra_str(s.action) == __pytra_str("store_true")) {
            __pytra_set_index(values, s.dest, __pytra_ifexp((s.default_ == nil), __pytra_truthy(s.default_), false))
        } else {
            if (s.default_ == nil) {
                __pytra_set_index(values, s.dest, s.default_)
            } else {
                __pytra_set_index(values, s.dest, nil)
            }
        }
    }
    var pos_i int64 = int64(0)
    var i int64 = int64(0)
    for (i < __pytra_len(args)) {
        var tok string = __pytra_str(__pytra_str(__pytra_get_index(args, i)))
        if __pytra_truthy(tok.startswith("-")) {
            if ((!__pytra_contains(by_name, tok))) {
                self._fail(nil)
            }
            var spec *_ArgSpec = __pytra_as__ArgSpec(__pytra_as__ArgSpec(__pytra_get_index(specs_opt, __pytra_int(__pytra_get_index(by_name, tok)))))
            if (__pytra_str(spec.action) == __pytra_str("store_true")) {
                __pytra_set_index(values, spec.dest, true)
                i += int64(1)
                continue
            }
            if ((i + int64(1)) >= __pytra_len(args)) {
                self._fail(nil)
            }
            var val string = __pytra_str(__pytra_str(__pytra_get_index(args, (i + int64(1)))))
            if ((__pytra_len(spec.choices) > int64(0)) && ((!__pytra_contains(spec.choices, val)))) {
                self._fail(nil)
            }
            __pytra_set_index(values, spec.dest, val)
            i += int64(2)
            continue
        }
        if (pos_i >= __pytra_len(specs_pos)) {
            self._fail(nil)
        }
        var spec *_ArgSpec = __pytra_as__ArgSpec(__pytra_as__ArgSpec(__pytra_get_index(specs_pos, pos_i)))
        __pytra_set_index(values, spec.dest, tok)
        pos_i += int64(1)
        i += int64(1)
    }
    if (pos_i < __pytra_len(specs_pos)) {
        self._fail(nil)
    }
    return __pytra_as_dict(values)
}
