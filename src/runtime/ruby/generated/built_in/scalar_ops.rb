# AUTO-GENERATED FILE. DO NOT EDIT.
# source: src/pytra/built_in/scalar_ops.py
# generated-by: tools/gen_runtime_from_manifest.py

require_relative "py_runtime"


def py_to_int64_base(v, base)
  return __b.int(v, base)
end

def py_ord(ch)
  return __b.ord(ch)
end

def py_chr(codepoint)
  return __b.chr(codepoint)
end

if __FILE__ == $PROGRAM_NAME
end
