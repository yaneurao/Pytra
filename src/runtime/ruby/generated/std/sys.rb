# AUTO-GENERATED FILE. DO NOT EDIT.
# source: src/pytra/std/sys.py
# generated-by: tools/gen_runtime_from_manifest.py

require_relative "py_runtime"


def exit(code)
  __s.exit(code)
end

def set_argv(values)
  argv.clear()
  for v in __pytra_as_list(values)
    argv.append(v)
  end
end

def set_path(values)
  path.clear()
  for v in __pytra_as_list(values)
    path.append(v)
  end
end

def write_stderr(text)
  __s.stderr.write(text)
end

def write_stdout(text)
  __s.stdout.write(text)
end

if __FILE__ == $PROGRAM_NAME
end
