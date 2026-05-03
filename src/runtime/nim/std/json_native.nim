import std/json
import std/strutils
import std/tables
import py_runtime

type JsonVal* = PyObj

type JsonValue* = ref object
  raw*: PyObj

type JsonArr* = ref object
  raw*: seq[PyObj]
  jsonarr_val*: JsonArr

type JsonObj* = ref object
  raw*: Table[string, PyObj]
  jsonobj_val*: JsonObj

converter toJsonValue*(raw: PyObj): JsonValue =
  JsonValue(raw: raw)

converter toJsonValue*(raw: Table[string, PyObj]): JsonValue =
  JsonValue(raw: py_box(raw))

converter toJsonValue*(raw: seq[PyObj]): JsonValue =
  JsonValue(raw: py_box(raw))

proc as_str*(value: JsonValue): PyObj =
  if value.isNil or value.raw.isNil:
    return nil
  if value.raw != nil and value.raw of PyStrObj:
    return value.raw
  return nil

proc as_int*(value: JsonValue): PyObj =
  if value.isNil or value.raw.isNil:
    return nil
  if value.raw of PyIntObj:
    return value.raw
  return nil

proc as_float*(value: JsonValue): PyObj =
  if value.isNil or value.raw.isNil:
    return nil
  if value.raw of PyFloatObj:
    return value.raw
  return nil

proc as_bool*(value: JsonValue): PyObj =
  if value.isNil or value.raw.isNil:
    return nil
  if value.raw of PyBoolObj:
    return value.raw
  return nil

proc as_arr*(value: JsonValue): JsonArr =
  if value.isNil or value.raw.isNil:
    return nil
  if value.raw != nil and value.raw of PyListObj:
    result = JsonArr(raw: PyListObj(value.raw).value)
    result.jsonarr_val = result
    return result
  return nil

proc as_obj*(value: JsonValue): JsonObj =
  if value.isNil or value.raw.isNil:
    return nil
  if value.raw != nil and value.raw of PyDictObj:
    result = JsonObj(raw: PyDictObj(value.raw).value)
    result.jsonobj_val = result
    return result
  return nil

proc get*(obj: JsonObj, key: string): JsonValue =
  if obj.isNil or not obj.raw.hasKey(key):
    return nil
  return JsonValue(raw: obj.raw[key])

proc get_obj*(obj: JsonObj, key: string): JsonObj =
  let value = obj.get(key)
  if value.isNil:
    return nil
  return value.as_obj()

proc get_arr*(obj: JsonObj, key: string): JsonArr =
  let value = obj.get(key)
  if value.isNil:
    return nil
  return value.as_arr()

proc get_str*(obj: JsonObj, key: string): PyObj =
  let value = obj.get(key)
  if value.isNil:
    return nil
  return value.as_str()

proc get_int*(obj: JsonObj, key: string): PyObj =
  let value = obj.get(key)
  if value.isNil:
    return nil
  return value.as_int()

proc get_float*(obj: JsonObj, key: string): PyObj =
  let value = obj.get(key)
  if value.isNil:
    return nil
  return value.as_float()

proc get_bool*(obj: JsonObj, key: string): PyObj =
  let value = obj.get(key)
  if value.isNil:
    return nil
  return value.as_bool()

proc get*(arr: JsonArr, index: int): JsonValue =
  if arr.isNil or index < 0 or index >= arr.raw.len:
    return nil
  return JsonValue(raw: arr.raw[index])

proc get_obj*(arr: JsonArr, index: int): JsonObj =
  let value = arr.get(index)
  if value.isNil:
    return nil
  return value.as_obj()

proc get_arr*(arr: JsonArr, index: int): JsonArr =
  let value = arr.get(index)
  if value.isNil:
    return nil
  return value.as_arr()

proc get_str*(arr: JsonArr, index: int): PyObj =
  let value = arr.get(index)
  if value.isNil:
    return nil
  return value.as_str()

proc get_int*(arr: JsonArr, index: int): PyObj =
  let value = arr.get(index)
  if value.isNil:
    return nil
  return value.as_int()

proc get_float*(arr: JsonArr, index: int): PyObj =
  let value = arr.get(index)
  if value.isNil:
    return nil
  return value.as_float()

proc get_bool*(arr: JsonArr, index: int): PyObj =
  let value = arr.get(index)
  if value.isNil:
    return nil
  return value.as_bool()

proc loads*(text: string): JsonValue =
  JsonValue(raw: py_box(parseJson(text)))

proc loads_arr*(text: string): JsonArr =
  loads(text).as_arr()

proc loads_obj*(text: string): JsonObj =
  loads(text).as_obj()

proc asciiEscapeJson(text: string): string =
  result = ""
  for ch in text:
    let code = ord(ch)
    case ch
    of '"':
      result.add("\\\"")
    of '\\':
      result.add("\\\\")
    of '\b':
      result.add("\\b")
    of '\f':
      result.add("\\f")
    of '\n':
      result.add("\\n")
    of '\r':
      result.add("\\r")
    of '\t':
      result.add("\\t")
    else:
      if code > 0x7F:
        result.add("\\u" & toHex(code, 4).toLowerAscii())
      else:
        result.add($ch)

proc dumpJsonNode(node: JsonNode, ensure_ascii: bool, indent: int, level: int): string

proc dumpJsonArray(node: JsonNode, ensure_ascii: bool, indent: int, level: int): string =
  if node.len == 0:
    return "[]"
  if indent < 0:
    var parts: seq[string] = @[]
    for item in node.items:
      parts.add(dumpJsonNode(item, ensure_ascii, indent, level + 1))
    return "[" & parts.join(",") & "]"
  let child_indent = repeat(" ", indent * (level + 1))
  let current_indent = repeat(" ", indent * level)
  var parts: seq[string] = @[]
  for item in node.items:
    parts.add(child_indent & dumpJsonNode(item, ensure_ascii, indent, level + 1))
  return "[\n" & parts.join(",\n") & "\n" & current_indent & "]"

proc dumpJsonObject(node: JsonNode, ensure_ascii: bool, indent: int, level: int): string =
  if node.len == 0:
    return "{}"
  if indent < 0:
    var parts: seq[string] = @[]
    for key, value in node.pairs:
      let key_text = "\"" & asciiEscapeJson(key) & "\""
      parts.add(key_text & ":" & dumpJsonNode(value, ensure_ascii, indent, level + 1))
    return "{" & parts.join(",") & "}"
  let child_indent = repeat(" ", indent * (level + 1))
  let current_indent = repeat(" ", indent * level)
  var parts: seq[string] = @[]
  for key, value in node.pairs:
    let key_text = "\"" & asciiEscapeJson(key) & "\""
    parts.add(child_indent & key_text & ": " & dumpJsonNode(value, ensure_ascii, indent, level + 1))
  return "{\n" & parts.join(",\n") & "\n" & current_indent & "}"

proc dumpJsonNode(node: JsonNode, ensure_ascii: bool, indent: int, level: int): string =
  case node.kind
  of JNull:
    "null"
  of JBool:
    if node.getBool(): "true" else: "false"
  of JInt:
    $node.getInt()
  of JFloat:
    $node.getFloat()
  of JString:
    if ensure_ascii:
      "\"" & asciiEscapeJson(node.getStr()) & "\""
    else:
      escapeJson(node.getStr())
  of JArray:
    dumpJsonArray(node, ensure_ascii, indent, level)
  of JObject:
    dumpJsonObject(node, ensure_ascii, indent, level)

proc dumps*(obj: JsonNode, ensure_ascii: bool = true, indent: PyObj = nil, separators: PyObj = nil): string =
  let indent_value = if indent.isNil: -1 else: py_int(indent)
  discard separators
  dumpJsonNode(obj, ensure_ascii, indent_value, 0)

proc dumps*(obj: string, ensure_ascii: bool = true, indent: PyObj = nil, separators: PyObj = nil): string =
  discard indent
  discard separators
  if ensure_ascii:
    return "\"" & asciiEscapeJson(obj) & "\""
  return escapeJson(obj)

proc dumps*(obj: bool, ensure_ascii: bool = true, indent: PyObj = nil, separators: PyObj = nil): string =
  discard ensure_ascii
  discard indent
  discard separators
  if obj:
    return "true"
  return "false"

proc dumps*(obj: int, ensure_ascii: bool = true, indent: PyObj = nil, separators: PyObj = nil): string =
  discard ensure_ascii
  discard indent
  discard separators
  $obj

proc dumps*(obj: int64, ensure_ascii: bool = true, indent: PyObj = nil, separators: PyObj = nil): string =
  discard ensure_ascii
  discard indent
  discard separators
  $obj

proc pyObjToJsonNode(obj: PyObj): JsonNode =
  if obj.isNil:
    return newJNull()
  if obj of PyStrObj:
    return newJString(PyStrObj(obj).value)
  if obj of PyBoolObj:
    return newJBool(PyBoolObj(obj).value)
  if obj of PyIntObj:
    return newJInt(PyIntObj(obj).value)
  if obj of PyFloatObj:
    return newJFloat(PyFloatObj(obj).value)
  if obj of PyListObj:
    result = newJArray()
    for item in PyListObj(obj).value:
      result.add(pyObjToJsonNode(item))
    return result
  if obj of PyDictObj:
    result = newJObject()
    for key, value in PyDictObj(obj).value:
      result[key] = pyObjToJsonNode(value)
    return result
  return newJString(py_to_string(obj))

proc dumps*(obj: seq[PyObj], ensure_ascii: bool = true, indent: PyObj = nil, separators: PyObj = nil): string =
  var arr = newJArray()
  for item in obj:
    arr.add(pyObjToJsonNode(item))
  dumps(arr, ensure_ascii, indent, separators)

proc dumps*(obj: Table[string, PyObj], ensure_ascii: bool = true, indent: PyObj = nil, separators: PyObj = nil): string =
  var table_obj = newJObject()
  for key, value in obj:
    table_obj[key] = pyObjToJsonNode(value)
  dumps(table_obj, ensure_ascii, indent, separators)

proc dumps*(obj: PyObj, ensure_ascii: bool = true, indent: PyObj = nil, separators: PyObj = nil): string =
  dumps(pyObjToJsonNode(obj), ensure_ascii, indent, separators)

proc dumps*(obj: JsonArr, ensure_ascii: bool = true, indent: PyObj = nil, separators: PyObj = nil): string =
  dumps(obj.raw, ensure_ascii, indent, separators)

proc dumps*(obj: JsonValue, ensure_ascii: bool = true, indent: PyObj = nil, separators: PyObj = nil): string =
  dumps(obj.raw, ensure_ascii, indent, separators)

proc dumps_jv*(jv: PyObj, ensure_ascii: bool = true, indent: PyObj = nil, separators: PyObj = nil): string =
  dumps(jv, ensure_ascii, indent, separators)
