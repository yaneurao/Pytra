# AUTO-GENERATED FILE. DO NOT EDIT.
# source: src/pytra/utils/png.py
# source: src/pytra/utils/gif.py
# generated-by: tools/gen_image_runtime_from_canonical.py

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

proc pytraGifLzwEncode(data: seq[uint8], minCodeSize: int = 8): seq[uint8] =
  if data.len == 0:
    return @[]

  let clearCode = 1 shl minCodeSize
  let endCode = clearCode + 1
  let codeSize = minCodeSize + 1

  var buf: seq[uint8] = @[]
  var bitBuffer = 0
  var bitCount = 0

  proc emitCode(code: int, bits: int) =
    bitBuffer = bitBuffer or (code shl bitCount)
    bitCount += bits
    while bitCount >= 8:
      buf.add(uint8(bitBuffer and 0xFF))
      bitBuffer = bitBuffer shr 8
      bitCount -= 8

  emitCode(clearCode, codeSize)
  var i = 0
  while i < data.len:
    emitCode(int(data[i]), codeSize)
    emitCode(clearCode, codeSize)
    inc i
  emitCode(endCode, codeSize)
  if bitCount > 0:
    buf.add(uint8(bitBuffer and 0xFF))
  result = buf

proc grayscale_palette*(): seq[uint8] =
  result = @[]
  var i = 0
  while i < 256:
    let b = uint8(i)
    result.add(b)
    result.add(b)
    result.add(b)
    inc i

proc save_gif*(
  path: string,
  width: int,
  height: int,
  frames: seq[seq[uint8]],
  palette: seq[uint8],
  delay_cs: int = 4,
  loop: int = 0,
) =
  let framePixels = width * height
  if palette.len != 256 * 3:
    raise newException(ValueError, "palette must be 256*3 bytes")

  var i = 0
  while i < frames.len:
    if frames[i].len != framePixels:
      raise newException(ValueError, "frame size mismatch")
    inc i

  var buf: seq[uint8] = @[]
  buf.add(@[0x47'u8, 0x49'u8, 0x46'u8, 0x38'u8, 0x39'u8, 0x61'u8]) # GIF89a
  buf.add(pytraU16le(width))
  buf.add(pytraU16le(height))
  buf.add(0xF7'u8)
  buf.add(0'u8)
  buf.add(0'u8)
  buf.add(palette)

  buf.add(@[0x21'u8, 0xFF'u8, 0x0B'u8])
  for ch in "NETSCAPE2.0":
    buf.add(uint8(ord(ch)))
  buf.add(@[0x03'u8, 0x01'u8])
  buf.add(pytraU16le(loop))
  buf.add(0'u8)

  i = 0
  while i < frames.len:
    let fr = frames[i]
    buf.add(@[0x21'u8, 0xF9'u8, 0x04'u8, 0x00'u8])
    buf.add(pytraU16le(delay_cs))
    buf.add(@[0x00'u8, 0x00'u8])

    buf.add(0x2C'u8)
    buf.add(pytraU16le(0))
    buf.add(pytraU16le(0))
    buf.add(pytraU16le(width))
    buf.add(pytraU16le(height))
    buf.add(0'u8)

    buf.add(8'u8)
    let compressed = pytraGifLzwEncode(fr, 8)
    var pos = 0
    while pos < compressed.len:
      let remain = compressed.len - pos
      let chunkLen = (if remain > 255: 255 else: remain)
      buf.add(uint8(chunkLen))
      var j = 0
      while j < chunkLen:
        buf.add(compressed[pos + j])
        inc j
      pos += chunkLen
    buf.add(0'u8)
    inc i

  buf.add(0x3B'u8)
  pytraWriteBytes(path, buf)
