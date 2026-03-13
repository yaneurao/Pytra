# AUTO-GENERATED FILE. DO NOT EDIT.
# source: src/pytra/std/argparse.py
# generated-by: tools/gen_runtime_from_manifest.py

include "py_runtime.nim"

import std/os, std/times, std/tables, std/strutils, std/math, std/sequtils

discard "Minimal pure-Python argparse subset for selfhost usage."
type Namespace* = ref object
  values*: Table[string, auto]


proc newNamespace*(values: auto): Namespace =
  new(result)
  if (values == nil):
    result.values = initTable[string, int]()
    return 
  result.values = values

type vArgSpec* = ref object
  names*: seq[string]
  action*: string
  choices*: seq[string]
  default*: int
  help_text*: string
  is_optional*: bool
  dest*: string


proc newvArgSpec*(names: seq[string], action: string, choices: seq[string], default: auto, help_text: string): vArgSpec =
  new(result)
  result.names = names
  result.action = action
  result.choices = choices
  result.default = default
  result.help_text = help_text
  result.is_optional = ((names.len > 0) and py_truthy($(names[0]).startswith("-")))
  if py_truthy(result.is_optional):
    var base = $(names[(names.len + (-1))]).lstrip("-").replace("-", "_")
    result.dest = base
  else:
    result.dest = $(names[0])

type ArgumentParser* = ref object
  description*: string
  vspecs*: seq[auto]

proc add_argument*(self: ArgumentParser, name0: string, name1: string, name2: string, name3: string, help: string, action: string, choices: seq[string], default: auto)
proc vfail*(self: ArgumentParser, msg: string)
proc parse_args*(self: ArgumentParser, argv: auto): Table[string, auto]

proc newArgumentParser*(description: string): ArgumentParser =
  new(result)
  result.description = description
  result.vspecs = @[] # seq[auto]

proc add_argument*(self: ArgumentParser, name0: string, name1: string, name2: string, name3: string, help: string, action: string, choices: seq[string], default: auto) =
  var names: seq[string] = @[]
  names = @[] # seq[string]
  if (name0 != ""):
    names.add(name0)
  if (name1 != ""):
    names.add(name1)
  if (name2 != ""):
    names.add(name2)
  if (name3 != ""):
    names.add(name3)
  if (names.len == 0):
    raise newException(Exception, "add_argument requires at least one name")
  var spec = vArgSpec(names, action, choices, default, help)
  self.vspecs.add(spec)

proc vfail*(self: ArgumentParser, msg: string) =
  if (msg != ""):
    sys.write_stderr(0)
  raise newException(Exception, SystemExit(2))

proc parse_args*(self: ArgumentParser, argv: auto): Table[string, auto] =
  var args: seq[string] = @[]
  var by_name: Table[string, int] = initTable[string, int]()
  var i: int = 0
  var pos_i: int = 0
  var spec_i: int = 0
  var specs_opt: seq[auto] = @[]
  var specs_pos: seq[auto] = @[]
  var tok: string = ""
  var val: string = ""
  var values: Table[string, auto] = initTable[string, int]()
  discard args # seq[string]
  if (argv == nil):
    args = sys.argv[1 ..< (sys.argv.len)]
  else:
    args = list(argv)
  specs_pos = @[] # seq[auto]
  specs_opt = @[] # seq[auto]
  for s in self.vspecs:
    if py_truthy(s.is_optional):
      specs_opt.add(s)
    else:
      specs_pos.add(s)
  by_name = initTable[string, int]() # Table[string, int]
  spec_i = 0
  for s in specs_opt:
    for n in s.names:
      by_name[n] = spec_i
    spec_i += 1
  values = initTable[string, int]() # Table[string, auto]
  for s in self.vspecs:
    if (s.action == "store_true"):
      values[s.dest] = (if (s.default == nil): py_truthy(s.default) else: false)
    elif (s.default == nil):
      values[s.dest] = s.default
    else:
      values[s.dest] = nil
  pos_i = 0
  i = 0
  while (i < args.len):
    tok = $(args[i])
    if py_truthy(tok.startswith("-")):
      if (not hasKey(by_name, tok)):
        self.vfail(0)
      var spec = specs_opt[by_name[tok]]
      if (spec.action == "store_true"):
        values[spec.dest] = true
        i += 1
        continue
      if ((i + 1) >= args.len):
        self.vfail(0)
      val = $(args[(i + 1)])
      if py_truthy(((spec.choices.len > 0) and (not (val in spec.choices)))):
        self.vfail(0)
      values[spec.dest] = val
      i += 2
      continue
    if (pos_i >= specs_pos.len):
      self.vfail(0)
    var spec = specs_pos[pos_i]
    values[spec.dest] = tok
    pos_i += 1
    i += 1
  if (pos_i < specs_pos.len):
    self.vfail(0)
  return values
