# AUTO-GENERATED FILE. DO NOT EDIT.
# source: src/pytra/utils/png.py
# generated-by: tools/gen_runtime_from_manifest.py

include "py_runtime.nim"

import std/os, std/times, std/tables, std/strutils, std/math, std/sequtils

discard "PNG 書き出しユーティリティ（Python実行用）。\n\nこのモジュールは sample/py のスクリプトから利用し、\nRGB 8bit バッファを PNG ファイルとして保存する。\n"
proc vpng_append_list*(dst: seq[int], src: seq[int]) =
  var i: int = 0
  var n: int = 0
  i = 0
  n = src.len
  while (i < n):
    dst.add(src[i])
    i += 1

proc vcrc32*(data: seq[int]): int =
  var crc: int = 0
  var i: int = 0
  var lowbit: int = 0
  var poly: int = 0
  crc = 4294967295
  poly = 3988292384
  for b in data:
    crc = (crc xor b)
    i = 0
    while (i < 8):
      lowbit = (crc and 1)
      if (lowbit != 0):
        crc = ((crc shr 1) xor poly)
      else:
        crc = (crc shr 1)
      i += 1
  return (crc xor 4294967295)

proc vadler32*(data: seq[int]): int =
  var `mod`: int = 0
  var s1: int = 0
  var s2: int = 0
  `mod` = 65521
  s1 = 1
  s2 = 0
  for b in data:
    s1 += b
    if (s1 >= `mod`):
      s1 -= `mod`
    s2 += s1
    s2 = py_mod(int(s2), int(`mod`))
  return (((s2 shl 16) or s1) and 4294967295)

proc vpng_u16le*(v: int): seq[int] =
  return @[(v and 255), ((v shr 8) and 255)]

proc vpng_u32be*(v: int): seq[int] =
  return @[((v shr 24) and 255), ((v shr 16) and 255), ((v shr 8) and 255), (v and 255)]

proc vzlib_deflate_store*(data: seq[int]): seq[int] =
  var `end`: int = 0
  var `out`: seq[int] = @[]
  var chunk_len: int = 0
  var final: int = 0
  var i: int = 0
  var n: int = 0
  var pos: int = 0
  var remain: int = 0
  `out` = @[] # seq[int]
  vpng_append_list(`out`, @[120, 1])
  n = data.len
  pos = 0
  while (pos < n):
    remain = (n - pos)
    chunk_len = (if (remain > 65535): 65535 else: remain)
    final = (if ((pos + chunk_len) >= n): 1 else: 0)
    `out`.add(final)
    vpng_append_list(`out`, vpng_u16le(chunk_len))
    vpng_append_list(`out`, vpng_u16le((65535 xor chunk_len)))
    i = pos
    `end` = (pos + chunk_len)
    while (i < `end`):
      `out`.add(data[i])
      i += 1
    pos += chunk_len
  vpng_append_list(`out`, vpng_u32be(vadler32(data)))
  return `out`

proc vchunk*(chunk_type: seq[int], data: seq[int]): seq[int] =
  var `out`: seq[int] = @[]
  var crc: int = 0
  var crc_input: seq[int] = @[]
  crc_input = @[] # seq[int]
  vpng_append_list(crc_input, chunk_type)
  vpng_append_list(crc_input, data)
  crc = (vcrc32(crc_input) and 4294967295)
  `out` = @[] # seq[int]
  vpng_append_list(`out`, vpng_u32be(data.len))
  vpng_append_list(`out`, chunk_type)
  vpng_append_list(`out`, data)
  vpng_append_list(`out`, vpng_u32be(crc))
  return `out`

proc write_rgb_png*(path: string, width: int, height: int, pixels: seq[uint8]) =
  var `end`: int = 0
  var expected: int = 0
  var i: int = 0
  var idat: seq[int] = @[]
  var iend_data: seq[int] = @[]
  var ihdr: seq[int] = @[]
  var png: seq[int] = @[]
  var raw: seq[int] = @[]
  var row_bytes: int = 0
  var scanlines: seq[int] = @[]
  var start: int = 0
  var y: int = 0
  raw = @[] # seq[int]
  for b in pixels:
    raw.add(int(b))
  expected = ((width * height) * 3)
  if (raw.len != expected):
    raise newException(Exception, ($(($(($("pixels length mismatch: got=") & $($( raw.len )))) & $(" expected="))) & $($( expected ))))
  scanlines = @[] # seq[int]
  row_bytes = (width * 3)
  y = 0
  while (y < height):
    scanlines.add(0)
    start = (y * row_bytes)
    `end` = (start + row_bytes)
    i = start
    while (i < `end`):
      scanlines.add(raw[i])
      i += 1
    y += 1
  ihdr = @[] # seq[int]
  vpng_append_list(ihdr, vpng_u32be(width))
  vpng_append_list(ihdr, vpng_u32be(height))
  vpng_append_list(ihdr, @[8, 2, 0, 0, 0])
  idat = vzlib_deflate_store(scanlines)
  png = @[] # seq[int]
  vpng_append_list(png, @[137, 80, 78, 71, 13, 10, 26, 10])
  vpng_append_list(png, vchunk(@[73, 72, 68, 82], ihdr))
  vpng_append_list(png, vchunk(@[73, 68, 65, 84], idat))
  iend_data = @[] # seq[int]
  vpng_append_list(png, vchunk(@[73, 69, 78, 68], iend_data))
  var f = open(path, "wb")
  # unsupported stmt: Try
