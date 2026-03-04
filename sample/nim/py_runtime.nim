# Nim runtime for Pytra
import std/os
import std/times
import std/tables
import std/strutils
import std/math

proc py_perf_counter*(): float =
  epochTime()

# Pytra built-ins
proc py_int*(v: auto): int =
  when v is string:
    parseInt(v)
  else:
    int(v)

proc py_float*(v: auto): float =
  when v is string:
    parseFloat(v)
  else:
    float(v)

proc py_str*(v: auto): string =
  $v

proc py_len*(v: seq or string or Table): int =
  v.len

template py_truthy*(v: auto): bool =
  when v is bool:
    v
  elif v is int or v is float:
    v != 0
  elif v is string or v is seq or v is Table:
    v.len > 0
  else:
    not v.isNil

# Python-style modulo
proc py_mod*[T: int or float](a, b: T): T =
  if b == 0:
    return 0
  let r = a mod b
  if (r > 0 and b < 0) or (r < 0 and b > 0):
    r + b
  else:
    r

proc pytraU16le(v: int): seq[uint8] =
  let x = v and 0xFFFF
  result = @[uint8(x and 0xFF), uint8((x shr 8) and 0xFF)]

proc pytraU32be(v: int): seq[uint8] =
  let x = v and 0xFFFFFFFF
  result = @[
    uint8((x shr 24) and 0xFF),
    uint8((x shr 16) and 0xFF),
    uint8((x shr 8) and 0xFF),
    uint8(x and 0xFF),
  ]

proc pytraCrc32(data: seq[uint8]): uint32 =
  var crc: uint32 = 0xFFFFFFFF'u32
  const poly: uint32 = 0xEDB88320'u32
  for b in data:
    crc = crc xor uint32(b)
    var i = 0
    while i < 8:
      if (crc and 1'u32) != 0'u32:
        crc = (crc shr 1) xor poly
      else:
        crc = crc shr 1
      inc i
  result = crc xor 0xFFFFFFFF'u32

proc pytraAdler32(data: seq[uint8]): uint32 =
  const modAdler = 65521
  var s1 = 1
  var s2 = 0
  for b in data:
    s1 += int(b)
    if s1 >= modAdler:
      s1 -= modAdler
    s2 += s1
    s2 = s2 mod modAdler
  result = uint32(((s2 shl 16) or s1) and 0xFFFFFFFF)

proc pytraZlibDeflateStore(data: seq[uint8]): seq[uint8] =
  result = @[0x78'u8, 0x01'u8]
  let n = data.len
  var pos = 0
  while pos < n:
    let remain = n - pos
    let chunkLen = (if remain > 65535: 65535 else: remain)
    let finalFlag = (if (pos + chunkLen) >= n: 1'u8 else: 0'u8)
    result.add(finalFlag)
    result.add(pytraU16le(chunkLen))
    result.add(pytraU16le(0xFFFF xor chunkLen))
    var i = pos
    let stopPos = pos + chunkLen
    while i < stopPos:
      result.add(data[i])
      inc i
    pos = stopPos
  result.add(pytraU32be(int(pytraAdler32(data))))

proc pytraPngChunk(chunkType: seq[uint8], data: seq[uint8]): seq[uint8] =
  result = @[]
  result.add(pytraU32be(data.len))
  result.add(chunkType)
  result.add(data)
  var crcInput: seq[uint8] = @[]
  crcInput.add(chunkType)
  crcInput.add(data)
  result.add(pytraU32be(int(pytraCrc32(crcInput))))

proc pytraWriteBytes(path: string, bytes: seq[uint8]) =
  var f = open(path, fmWrite)
  defer:
    f.close()
  if bytes.len > 0:
    discard writeBytes(f, bytes, 0, bytes.len)

proc write_rgb_png*(path: string, width: int, height: int, pixels: seq[uint8]) =
  let expected = width * height * 3
  if pixels.len != expected:
    raise newException(
      ValueError,
      "pixels length mismatch: got=" & $pixels.len & " expected=" & $expected,
    )

  var scanlines: seq[uint8] = @[]
  let rowBytes = width * 3
  var y = 0
  while y < height:
    scanlines.add(0'u8)
    let start = y * rowBytes
    let stopPos = start + rowBytes
    var i = start
    while i < stopPos:
      scanlines.add(pixels[i])
      inc i
    inc y

  var ihdr: seq[uint8] = @[]
  ihdr.add(pytraU32be(width))
  ihdr.add(pytraU32be(height))
  ihdr.add(@[8'u8, 2'u8, 0'u8, 0'u8, 0'u8])
  let idat = pytraZlibDeflateStore(scanlines)

  var png: seq[uint8] = @[0x89'u8, 0x50'u8, 0x4E'u8, 0x47'u8, 0x0D'u8, 0x0A'u8, 0x1A'u8, 0x0A'u8]
  png.add(pytraPngChunk(@[0x49'u8, 0x48'u8, 0x44'u8, 0x52'u8], ihdr))
  png.add(pytraPngChunk(@[0x49'u8, 0x44'u8, 0x41'u8, 0x54'u8], idat))
  png.add(pytraPngChunk(@[0x49'u8, 0x45'u8, 0x4E'u8, 0x44'u8], @[]))
  pytraWriteBytes(path, png)
