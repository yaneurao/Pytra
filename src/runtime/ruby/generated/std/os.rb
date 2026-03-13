# AUTO-GENERATED FILE. DO NOT EDIT.
# source: src/pytra/std/os.py
# generated-by: tools/gen_runtime_from_manifest.py

require_relative "py_runtime"


def getcwd()
  return __os.getcwd()
end

def mkdir(p)
  __os.mkdir(p)
end

def makedirs(p, exist_ok)
  __os.makedirs(p)
end

if __FILE__ == $PROGRAM_NAME
end
