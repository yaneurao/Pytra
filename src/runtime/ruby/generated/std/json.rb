# AUTO-GENERATED FILE. DO NOT EDIT.
# source: src/pytra/std/json.py
# generated-by: tools/gen_runtime_from_manifest.py

require_relative "py_runtime"


class JsonObj
  attr_accessor :raw

  def initialize(raw)
    self.raw = raw
  end

  def get(key)
    if !__pytra_contains(self.raw, key)
      return nil
    end
    value = _json_obj_require(self.raw, key)
    return JsonValue.new(value)
  end

  def get_obj(key)
    if !__pytra_contains(self.raw, key)
      return nil
    end
    value = _json_obj_require(self.raw, key)
    return JsonValue.new(value).as_obj()
  end

  def get_arr(key)
    if !__pytra_contains(self.raw, key)
      return nil
    end
    value = _json_obj_require(self.raw, key)
    return JsonValue.new(value).as_arr()
  end

  def get_str(key)
    if !__pytra_contains(self.raw, key)
      return nil
    end
    value = _json_obj_require(self.raw, key)
    return JsonValue.new(value).as_str()
  end

  def get_int(key)
    if !__pytra_contains(self.raw, key)
      return nil
    end
    value = _json_obj_require(self.raw, key)
    return JsonValue.new(value).as_int()
  end

  def get_float(key)
    if !__pytra_contains(self.raw, key)
      return nil
    end
    value = _json_obj_require(self.raw, key)
    return JsonValue.new(value).as_float()
  end

  def get_bool(key)
    if !__pytra_contains(self.raw, key)
      return nil
    end
    value = _json_obj_require(self.raw, key)
    return JsonValue.new(value).as_bool()
  end
end

class JsonArr
  attr_accessor :raw

  def initialize(raw)
    self.raw = raw
  end

  def get(index)
    if (index < 0) || (index >= __pytra_len(_json_array_items(self.raw)))
      return nil
    end
    return JsonValue.new(__pytra_get_index(_json_array_items(self.raw), index))
  end

  def get_obj(index)
    if (index < 0) || (index >= __pytra_len(_json_array_items(self.raw)))
      return nil
    end
    return JsonValue.new(__pytra_get_index(_json_array_items(self.raw), index)).as_obj()
  end

  def get_arr(index)
    if (index < 0) || (index >= __pytra_len(_json_array_items(self.raw)))
      return nil
    end
    return JsonValue.new(__pytra_get_index(_json_array_items(self.raw), index)).as_arr()
  end

  def get_str(index)
    if (index < 0) || (index >= __pytra_len(_json_array_items(self.raw)))
      return nil
    end
    return JsonValue.new(__pytra_get_index(_json_array_items(self.raw), index)).as_str()
  end

  def get_int(index)
    if (index < 0) || (index >= __pytra_len(_json_array_items(self.raw)))
      return nil
    end
    return JsonValue.new(__pytra_get_index(_json_array_items(self.raw), index)).as_int()
  end

  def get_float(index)
    if (index < 0) || (index >= __pytra_len(_json_array_items(self.raw)))
      return nil
    end
    return JsonValue.new(__pytra_get_index(_json_array_items(self.raw), index)).as_float()
  end

  def get_bool(index)
    if (index < 0) || (index >= __pytra_len(_json_array_items(self.raw)))
      return nil
    end
    return JsonValue.new(__pytra_get_index(_json_array_items(self.raw), index)).as_bool()
  end
end

class JsonValue
  attr_accessor :raw

  def initialize(raw)
    self.raw = raw
  end

  def as_obj()
    raw = self.raw
    if false
      raw_obj = __pytra_as_dict(raw)
      return JsonObj.new(raw_obj)
    end
    return nil
  end

  def as_arr()
    raw = self.raw
    if false
      raw_arr = __pytra_as_list(raw)
      return JsonArr.new(raw_arr)
    end
    return nil
  end

  def as_str()
    raw = self.raw
    if false
      return raw
    end
    return nil
  end

  def as_int()
    raw = self.raw
    if false
      return nil
    end
    if false
      raw_i = __pytra_int(raw)
      return raw_i
    end
    return nil
  end

  def as_float()
    raw = self.raw
    if false
      raw_f = __pytra_float(raw)
      return raw_f
    end
    return nil
  end

  def as_bool()
    raw = self.raw
    if false
      raw_b = __pytra_truthy(raw)
      return raw_b
    end
    return nil
  end
end

class JsonParser
  attr_accessor :text, :n, :i

  def initialize(text)
    self.text = text
    self.n = __pytra_len(text)
    self.i = 0
  end

  def parse()
    self._skip_ws()
    out = self._parse_value()
    self._skip_ws()
    if self.i != self.n
      raise RuntimeError, __pytra_str("invalid json: trailing characters")
    end
    return out
  end

  def _skip_ws()
    while (self.i < self.n) && _is_ws(__pytra_get_index(self.text, self.i))
      self.i += 1
    end
  end

  def _parse_value()
    if self.i >= self.n
      raise RuntimeError, __pytra_str("invalid json: unexpected end")
    end
    ch = __pytra_get_index(self.text, self.i)
    if ch == "{"
      return self._parse_object()
    end
    if ch == "["
      return self._parse_array()
    end
    if ch == "\""
      return self._parse_string()
    end
    if (ch == "t") && (__pytra_slice(self.text, self.i, self.i + 4) == "true")
      self.i += 4
      return true
    end
    if (ch == "f") && (__pytra_slice(self.text, self.i, self.i + 5) == "false")
      self.i += 5
      return false
    end
    if (ch == "n") && (__pytra_slice(self.text, self.i, self.i + 4) == "null")
      self.i += 4
      return nil
    end
    return self._parse_number()
  end

  def _parse_object()
    out = {}
    self.i += 1
    self._skip_ws()
    if (self.i < self.n) && (__pytra_get_index(self.text, self.i) == "}")
      self.i += 1
      return out
    end
    while true
      self._skip_ws()
      if (self.i >= self.n) || (__pytra_get_index(self.text, self.i) != "\"")
        raise RuntimeError, __pytra_str("invalid json object key")
      end
      key = self._parse_string()
      self._skip_ws()
      if (self.i >= self.n) || (__pytra_get_index(self.text, self.i) != ":")
        raise RuntimeError, __pytra_str("invalid json object: missing ':'")
      end
      self.i += 1
      self._skip_ws()
      __pytra_set_index(out, key, self._parse_value())
      self._skip_ws()
      if self.i >= self.n
        raise RuntimeError, __pytra_str("invalid json object: unexpected end")
      end
      ch = __pytra_get_index(self.text, self.i)
      self.i += 1
      if ch == "}"
        return out
      end
      if ch != ","
        raise RuntimeError, __pytra_str("invalid json object separator")
      end
    end
  end

  def _parse_array()
    out = _json_new_array()
    self.i += 1
    self._skip_ws()
    if (self.i < self.n) && (__pytra_get_index(self.text, self.i) == "]")
      self.i += 1
      return out
    end
    while true
      self._skip_ws()
      out.append(self._parse_value())
      self._skip_ws()
      if self.i >= self.n
        raise RuntimeError, __pytra_str("invalid json array: unexpected end")
      end
      ch = __pytra_get_index(self.text, self.i)
      self.i += 1
      if ch == "]"
        return out
      end
      if ch != ","
        raise RuntimeError, __pytra_str("invalid json array separator")
      end
    end
  end

  def _parse_string()
    if __pytra_get_index(self.text, self.i) != "\""
      raise RuntimeError, __pytra_str("invalid json string")
    end
    self.i += 1
    out_chars = []
    while self.i < self.n
      ch = __pytra_get_index(self.text, self.i)
      self.i += 1
      if ch == "\""
        return _join_strs(out_chars, _EMPTY)
      end
      if ch == "\\"
        if self.i >= self.n
          raise RuntimeError, __pytra_str("invalid json string escape")
        end
        esc = __pytra_get_index(self.text, self.i)
        self.i += 1
        if esc == "\""
          out_chars.append("\"")
        else
          if esc == "\\"
            out_chars.append("\\")
          else
            if esc == "/"
              out_chars.append("/")
            else
              if esc == "b"
                out_chars.append("")
              else
                if esc == "f"
                  out_chars.append("")
                else
                  if esc == "n"
                    out_chars.append("\n")
                  else
                    if esc == "r"
                      out_chars.append("")
                    else
                      if esc == "t"
                        out_chars.append("	")
                      else
                        if esc == "u"
                          if self.i + 4 > self.n
                            raise RuntimeError, __pytra_str("invalid json unicode escape")
                          end
                          hx = __pytra_slice(self.text, self.i, self.i + 4)
                          self.i += 4
                          out_chars.append(chr(_int_from_hex4(hx)))
                        else
                          raise RuntimeError, __pytra_str("invalid json escape")
                        end
                      end
                    end
                  end
                end
              end
            end
          end
        end
      else
        out_chars.append(ch)
      end
    end
    raise RuntimeError, __pytra_str("unterminated json string")
  end

  def _parse_number()
    start = self.i
    if __pytra_get_index(self.text, self.i) == "-"
      self.i += 1
    end
    if self.i >= self.n
      raise RuntimeError, __pytra_str("invalid json number")
    end
    if __pytra_get_index(self.text, self.i) == "0"
      self.i += 1
    else
      if !_is_digit(__pytra_get_index(self.text, self.i))
        raise RuntimeError, __pytra_str("invalid json number")
      end
      while (self.i < self.n) && _is_digit(__pytra_get_index(self.text, self.i))
        self.i += 1
      end
    end
    is_float = false
    if (self.i < self.n) && (__pytra_get_index(self.text, self.i) == ".")
      is_float = true
      self.i += 1
      if (self.i >= self.n) || (!_is_digit(__pytra_get_index(self.text, self.i)))
        raise RuntimeError, __pytra_str("invalid json number")
      end
      while (self.i < self.n) && _is_digit(__pytra_get_index(self.text, self.i))
        self.i += 1
      end
    end
    if self.i < self.n
      exp_ch = __pytra_get_index(self.text, self.i)
      if (exp_ch == "e") || (exp_ch == "E")
        is_float = true
        self.i += 1
        if self.i < self.n
          sign = __pytra_get_index(self.text, self.i)
          if (sign == "+") || (sign == "-")
            self.i += 1
          end
        end
        if (self.i >= self.n) || (!_is_digit(__pytra_get_index(self.text, self.i)))
          raise RuntimeError, __pytra_str("invalid json exponent")
        end
        while (self.i < self.n) && _is_digit(__pytra_get_index(self.text, self.i))
          self.i += 1
        end
      end
    end
    token = __pytra_slice(self.text, start, self.i)
    if is_float
      num_f = __pytra_float(token)
      return num_f
    end
    num_i = __pytra_int(token)
    return num_i
  end
end

def _is_ws(ch)
  return ((ch == " ") || (ch == "	") || (ch == "") || (ch == "\n"))
end

def _is_digit(ch)
  return ((ch >= "0") && (ch <= "9"))
end

def _hex_value(ch)
  if (ch >= "0") && (ch <= "9")
    return __pytra_int(ch)
  end
  if (ch == "a") || (ch == "A")
    return 10
  end
  if (ch == "b") || (ch == "B")
    return 11
  end
  if (ch == "c") || (ch == "C")
    return 12
  end
  if (ch == "d") || (ch == "D")
    return 13
  end
  if (ch == "e") || (ch == "E")
    return 14
  end
  if (ch == "f") || (ch == "F")
    return 15
  end
  raise RuntimeError, __pytra_str("invalid json unicode escape")
end

def _int_from_hex4(hx)
  if __pytra_len(hx) != 4
    raise RuntimeError, __pytra_str("invalid json unicode escape")
  end
  v0 = _hex_value(__pytra_slice(hx, 0, 1))
  v1 = _hex_value(__pytra_slice(hx, 1, 2))
  v2 = _hex_value(__pytra_slice(hx, 2, 3))
  v3 = _hex_value(__pytra_slice(hx, 3, 4))
  return (((v0 * 4096 + v1 * 256) + v2 * 16) + v3)
end

def _hex4(code)
  v = code % 65536
  d3 = v % 16
  v = v / 16
  d2 = v % 16
  v = v / 16
  d1 = v % 16
  v = v / 16
  d0 = v % 16
  p0 = __pytra_slice(_HEX_DIGITS, d0, d0 + 1)
  p1 = __pytra_slice(_HEX_DIGITS, d1, d1 + 1)
  p2 = __pytra_slice(_HEX_DIGITS, d2, d2 + 1)
  p3 = __pytra_slice(_HEX_DIGITS, d3, d3 + 1)
  return ((p0 + p1 + p2) + p3)
end

def _json_array_items(raw)
  return __pytra_as_list(raw)
end

def _json_new_array()
  return []
end

def _json_obj_require(raw, key)
  __iter_0 = __pytra_as_list(raw.items())
  for __it_1 in __iter_0
    __tuple_2 = __pytra_as_list(__it_1)
    k = __tuple_2[0]
    value = __tuple_2[1]
    if k == key
      return value
    end
  end
  raise RuntimeError, __pytra_str("json object key not found: " + key)
end

def _json_indent_value(indent)
  if indent == nil
    raise RuntimeError, __pytra_str("json indent is required")
  end
  indent_i = indent
  return indent_i
end

def loads(text)
  return JsonParser(text).parse()
end

def loads_obj(text)
  value = JsonParser(text).parse()
  if false
    raw_obj = __pytra_as_dict(value)
    return JsonObj.new(raw_obj)
  end
  return nil
end

def loads_arr(text)
  value = JsonParser(text).parse()
  if false
    raw_arr = __pytra_as_list(value)
    return JsonArr.new(raw_arr)
  end
  return nil
end

def _join_strs(parts, sep)
  if __pytra_len(parts) == 0
    return ""
  end
  out = __pytra_get_index(parts, 0)
  i = 1
  while i < __pytra_len(parts)
    out = (out + sep + __pytra_get_index(parts, i))
    i += 1
  end
  return out
end

def _escape_str(s, ensure_ascii)
  out = ["\""]
  for ch in __pytra_as_list(s)
    code = ord(ch)
    if ch == "\""
      out.append("\\\"")
    else
      if ch == "\\"
        out.append("\\\\")
      else
        if ch == ""
          out.append("\\b")
        else
          if ch == ""
            out.append("\\f")
          else
            if ch == "\n"
              out.append("\\n")
            else
              if ch == ""
                out.append("\\r")
              else
                if ch == "	"
                  out.append("\\t")
                else
                  if ensure_ascii && (code > 127)
                    out.append("\\u" + _hex4(code))
                  else
                    out.append(ch)
                  end
                end
              end
            end
          end
        end
      end
    end
  end
  out.append("\"")
  return _join_strs(out, _EMPTY)
end

def _dump_json_list(values, ensure_ascii, indent, item_sep, key_sep, level)
  if __pytra_len(values) == 0
    return "[]"
  end
  if indent == nil
    dumped = []
    for x in __pytra_as_list(values)
      dumped_txt = _dump_json_value(x, ensure_ascii, indent, item_sep, key_sep, level)
      dumped.append(dumped_txt)
    end
    return ("[" + _join_strs(dumped, item_sep) + "]")
  end
  indent_i = _json_indent_value(indent)
  inner = []
  for x in __pytra_as_list(values)
    prefix = (" " * (indent_i * (level + 1)))
    value_txt = _dump_json_value(x, ensure_ascii, indent, item_sep, key_sep, level + 1)
    inner.append(prefix + value_txt)
  end
  return ((("[\n" + _join_strs(inner, _COMMA_NL) + "\n") + (" " * indent_i * level)) + "]")
end

def _dump_json_dict(values, ensure_ascii, indent, item_sep, key_sep, level)
  if __pytra_len(values) == 0
    return "{}"
  end
  if indent == nil
    parts = []
    __iter_0 = __pytra_as_list(values.items())
    for __it_1 in __iter_0
      __tuple_2 = __pytra_as_list(__it_1)
      k = __tuple_2[0]
      x = __tuple_2[1]
      k_txt = _escape_str(__pytra_str(k), ensure_ascii)
      v_txt = _dump_json_value(x, ensure_ascii, indent, item_sep, key_sep, level)
      parts.append((k_txt + key_sep + v_txt))
    end
    return ("{" + _join_strs(parts, item_sep) + "}")
  end
  indent_i = _json_indent_value(indent)
  inner = []
  __iter_3 = __pytra_as_list(values.items())
  for __it_4 in __iter_3
    __tuple_5 = __pytra_as_list(__it_4)
    k = __tuple_5[0]
    x = __tuple_5[1]
    prefix = (" " * (indent_i * (level + 1)))
    k_txt = _escape_str(__pytra_str(k), ensure_ascii)
    v_txt = _dump_json_value(x, ensure_ascii, indent, item_sep, key_sep, level + 1)
    inner.append(((prefix + k_txt + key_sep) + v_txt))
  end
  return ((("{\n" + _join_strs(inner, _COMMA_NL) + "\n") + (" " * indent_i * level)) + "}")
end

def _dump_json_value(v, ensure_ascii, indent, item_sep, key_sep, level)
  if v == nil
    return "null"
  end
  if false
    raw_b = __pytra_truthy(v)
    return (raw_b ? "true" : "false")
  end
  if false
    return __pytra_str(v)
  end
  if false
    return __pytra_str(v)
  end
  if false
    return _escape_str(v, ensure_ascii)
  end
  if false
    as_list = __pytra_as_list(v)
    return _dump_json_list(as_list, ensure_ascii, indent, item_sep, key_sep, level)
  end
  if false
    as_dict = __pytra_as_dict(v)
    return _dump_json_dict(as_dict, ensure_ascii, indent, item_sep, key_sep, level)
  end
  raise RuntimeError, __pytra_str("json.dumps unsupported type")
end

def dumps(obj, ensure_ascii, indent, separators)
  item_sep = ","
  key_sep = ((indent == nil) ? ":" : ": ")
  if separators == nil
    __tuple_0 = __pytra_as_list(separators)
    item_sep = __tuple_0[0]
    key_sep = __tuple_0[1]
  end
  return _dump_json_value(obj, ensure_ascii, indent, item_sep, key_sep, 0)
end

if __FILE__ == $PROGRAM_NAME
end
