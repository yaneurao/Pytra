# AUTO-GENERATED FILE. DO NOT EDIT.
# source: src/pytra/std/os_path.py
# generated-by: tools/gen_runtime_from_manifest.py

require_relative "py_runtime"


def join(a, b)
  return __path.join(a, b)
end

def dirname(p)
  return __path.dirname(p)
end

def basename(p)
  return __path.basename(p)
end

def splitext(p)
  return __path.splitext(p)
end

def abspath(p)
  return __path.abspath(p)
end

def exists(p)
  return __path.exists(p)
end

if __FILE__ == $PROGRAM_NAME
end
