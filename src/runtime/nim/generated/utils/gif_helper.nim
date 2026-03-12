# AUTO-GENERATED FILE. DO NOT EDIT.
# source: src/pytra/utils/gif.py
# generated-by: tools/gen_runtime_from_manifest.py

include "py_runtime.nim"

import std/os, std/times, std/tables, std/strutils, std/math, std/sequtils

discard "アニメーションGIFを書き出すための最小ヘルパー。"
proc vgif_append_list*(dst: seq[int], src: seq[int]) =
  var i: int = 0
  var n: int = 0
  i = 0
  n = src.len
  while (i < n):
    dst.add(src[i])
    i += 1

proc vgif_u16le*(v: int): seq[int] =
  return @[(v and 255), ((v shr 8) and 255)]

proc vlzw_encode*(data: seq[uint8], min_code_size: int): seq[uint8] =
  var `out`: seq[int] = @[]
  var bit_buffer: int = 0
  var bit_count: int = 0
  var clear_code: int = 0
  var code_size: int = 0
  var end_code: int = 0
  if (data.len == 0):
    return @[]
  clear_code = (1 shl min_code_size)
  end_code = (clear_code + 1)
  code_size = (min_code_size + 1)
  `out` = @[] # seq[int]
  bit_buffer = 0
  bit_count = 0
  bit_buffer or= (clear_code shl bit_count)
  bit_count += code_size
  while (bit_count >= 8):
    `out`.add((bit_buffer and 255))
    bit_buffer = (bit_buffer shr 8)
    bit_count -= 8
  code_size = (min_code_size + 1)
  for v in data:
    bit_buffer or= (v shl bit_count)
    bit_count += code_size
    while (bit_count >= 8):
      `out`.add((bit_buffer and 255))
      bit_buffer = (bit_buffer shr 8)
      bit_count -= 8
    bit_buffer or= (clear_code shl bit_count)
    bit_count += code_size
    while (bit_count >= 8):
      `out`.add((bit_buffer and 255))
      bit_buffer = (bit_buffer shr 8)
      bit_count -= 8
    code_size = (min_code_size + 1)
  bit_buffer or= (end_code shl bit_count)
  bit_count += code_size
  while (bit_count >= 8):
    `out`.add((bit_buffer and 255))
    bit_buffer = (bit_buffer shr 8)
    bit_count -= 8
  if (bit_count > 0):
    `out`.add((bit_buffer and 255))
  return `out`

proc grayscale_palette*(): seq[uint8] =
  var i: int = 0
  var p: seq[int] = @[]
  p = @[] # seq[int]
  i = 0
  while (i < 256):
    p.add(i)
    p.add(i)
    p.add(i)
    i += 1
  return p

proc save_gif*(path: string, width: int, height: int, frames: seq[seq[uint8]], palette: seq[uint8], delay_cs: int, loop: int) =
  var `out`: seq[int] = @[]
  var chunk_len: int = 0
  var compressed: seq[uint8] = @[]
  var fr_list: seq[int] = @[]
  var frame_lists: seq[seq[int]] = @[]
  var i: int = 0
  var palette_list: seq[int] = @[]
  var pos: int = 0
  var remain: int = 0
  if (palette.len != (256 * 3)):
    raise newException(Exception, "palette must be 256*3 bytes")
  frame_lists = @[] # seq[seq[int]]
  for fr in frames:
    fr_list = @[]
    for v in fr:
      fr_list.add(int(v))
    if (fr_list.len != (width * height)):
      raise newException(Exception, "frame size mismatch")
    frame_lists.add(fr_list)
  palette_list = @[] # seq[int]
  for v in palette:
    palette_list.add(int(v))
  `out` = @[] # seq[int]
  vgif_append_list(`out`, @[71, 73, 70, 56, 57, 97])
  vgif_append_list(`out`, vgif_u16le(width))
  vgif_append_list(`out`, vgif_u16le(height))
  `out`.add(247)
  `out`.add(0)
  `out`.add(0)
  vgif_append_list(`out`, palette_list)
  vgif_append_list(`out`, @[33, 255, 11, 78, 69, 84, 83, 67, 65, 80, 69, 50, 46, 48, 3, 1])
  vgif_append_list(`out`, vgif_u16le(loop))
  `out`.add(0)
  for fr_list in frame_lists:
    vgif_append_list(`out`, @[33, 249, 4, 0])
    vgif_append_list(`out`, vgif_u16le(delay_cs))
    vgif_append_list(`out`, @[0, 0])
    `out`.add(44)
    vgif_append_list(`out`, vgif_u16le(0))
    vgif_append_list(`out`, vgif_u16le(0))
    vgif_append_list(`out`, vgif_u16le(width))
    vgif_append_list(`out`, vgif_u16le(height))
    `out`.add(0)
    `out`.add(8)
    compressed = vlzw_encode(fr_list, 8)
    pos = 0
    while (pos < compressed.len):
      remain = (compressed.len - pos)
      chunk_len = (if (remain > 255): 255 else: remain)
      `out`.add(chunk_len)
      i = 0
      while (i < chunk_len):
        `out`.add(compressed[(pos + i)])
        i += 1
      pos += chunk_len
    `out`.add(0)
  `out`.add(59)
  var f = open(path, "wb")
  # unsupported stmt: Try
