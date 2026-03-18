include "py_runtime.nim"

import std/os, std/times, std/tables, std/strutils, std/math, std/sequtils

discard "Pytra collections module — list-based deque implementation.\n\nProvides a deque compatible with all transpilation targets.\nBackends with native deque (C++ std::deque, Rust VecDeque, etc.)\ncan override this with emitter-level optimization.\n"
type Deque* = ref object
  vitems*: seq[int]

proc append*(self: Deque, value: int)
proc appendleft*(self: Deque, value: int)
proc pop*(self: Deque)
proc popleft*(self: Deque): int
proc v_len__*(self: Deque): int
proc clear*(self: Deque)

proc newDeque*(): Deque =
  new(result)
  result.vitems = @[] # seq[int]

proc append*(self: Deque, value: int) =
  self.vitems.add(value)

proc appendleft*(self: Deque, value: int) =
  self.vitems.insert(0, value)

proc pop*(self: Deque): auto =
  if (self.vitems.len == 0):
    raise newException(Exception, IndexError("pop from empty deque"))
  return self.vitems.pop()

proc popleft*(self: Deque): int =
  var item: int = 0
  if (self.vitems.len == 0):
    raise newException(Exception, IndexError("pop from empty deque"))
  item = self.vitems[0] # int
  self.vitems = self.vitems[1 ..< (self.vitems.len)]
  return item

proc v_len__*(self: Deque): int =
  return self.vitems.len

proc clear*(self: Deque) =
  self.vitems = @[]
