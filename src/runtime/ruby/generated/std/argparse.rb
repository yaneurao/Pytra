# AUTO-GENERATED FILE. DO NOT EDIT.
# source: src/pytra/std/argparse.py
# generated-by: tools/gen_runtime_from_manifest.py

require_relative "py_runtime"


class Namespace
  attr_accessor :values

  def initialize(values)
    if values == nil
      self.values = {}
      return nil
    end
    self.values = values
  end
end

class ArgSpec
  attr_accessor :names, :action, :choices, :default, :help_text, :is_optional, :dest

  def initialize(names, action, choices, default, help_text)
    self.names = names
    self.action = action
    self.choices = choices
    self.default = default
    self.help_text = help_text
    self.is_optional = ((__pytra_len(names) > 0) && __pytra_truthy(__pytra_get_index(names, 0).startswith("-")))
    if self.is_optional
      base = __pytra_get_index(names, (-1)).lstrip("-").replace("-", "_")
      self.dest = base
    else
      self.dest = __pytra_get_index(names, 0)
    end
  end
end

class ArgumentParser
  attr_accessor :description, :_specs

  def initialize(description)
    self.description = description
    self._specs = []
  end

  def add_argument(name0, name1, name2, name3, help, action, choices, default)
    names = []
    if name0 != ""
      names.append(name0)
    end
    if name1 != ""
      names.append(name1)
    end
    if name2 != ""
      names.append(name2)
    end
    if name3 != ""
      names.append(name3)
    end
    if __pytra_len(names) == 0
      raise RuntimeError, __pytra_str("add_argument requires at least one name")
    end
    spec = ArgSpec(names)
    self._specs.append(spec)
  end

  def _fail(msg)
    if msg != ""
      sys.write_stderr(nil)
    end
    raise RuntimeError, __pytra_str(SystemExit(2))
  end

  def parse_args(argv)
    args = nil
    if argv == nil
      args = __pytra_slice(sys.argv, 1, __pytra_len(sys.argv))
    else
      args = __pytra_as_list(argv)
    end
    specs_pos = []
    specs_opt = []
    for s in __pytra_as_list(self._specs)
      if __pytra_truthy(s.is_optional)
        specs_opt.append(s)
      else
        specs_pos.append(s)
      end
    end
    by_name = {}
    spec_i = 0
    for s in __pytra_as_list(specs_opt)
      for n in __pytra_as_list(s.names)
        __pytra_set_index(by_name, n, spec_i)
      end
      spec_i += 1
    end
    values = {}
    for s in __pytra_as_list(self._specs)
      if s.action == "store_true"
        __pytra_set_index(values, s.dest, ((s.default == nil) ? __pytra_truthy(s.default) : false))
      else
        if s.default == nil
          __pytra_set_index(values, s.dest, s.default)
        else
          __pytra_set_index(values, s.dest, nil)
        end
      end
    end
    pos_i = 0
    i = 0
    while i < __pytra_len(args)
      tok = __pytra_get_index(args, i)
      if __pytra_truthy(tok.startswith("-"))
        if !__pytra_contains(by_name, tok)
          self._fail(nil)
        end
        spec = __pytra_get_index(specs_opt, __pytra_get_index(by_name, tok))
        if spec.action == "store_true"
          __pytra_set_index(values, spec.dest, true)
          i += 1
          next
        end
        if i + 1 >= __pytra_len(args)
          self._fail(nil)
        end
        val = __pytra_get_index(args, i + 1)
        if (__pytra_len(spec.choices) > 0) && (!__pytra_contains(spec.choices, val))
          self._fail(nil)
        end
        __pytra_set_index(values, spec.dest, val)
        i += 2
        next
      end
      if pos_i >= __pytra_len(specs_pos)
        self._fail(nil)
      end
      spec = __pytra_get_index(specs_pos, pos_i)
      __pytra_set_index(values, spec.dest, tok)
      pos_i += 1
      i += 1
    end
    if pos_i < __pytra_len(specs_pos)
      self._fail(nil)
    end
    return values
  end
end

if __FILE__ == $PROGRAM_NAME
end
