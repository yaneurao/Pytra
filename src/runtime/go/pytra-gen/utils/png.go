// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/utils/png.py
// generated-by: tools/gen_image_runtime_from_canonical.py

package main

import (
	"bytes"
	"hash/crc32"
	"os"
)

func pyToBytes(v any) []byte {
	switch x := v.(type) {
	case []byte:
		out := make([]byte, len(x))
		copy(out, x)
		return out
	case []any:
		out := make([]byte, len(x))
		for i, e := range x {
			out[i] = byte(pyToInt(e))
		}
		return out
	case string:
		return []byte(x)
	default:
		panic("cannot convert to bytes")
	}
}

func pyChunk(chunkType []byte, data []byte) []byte {
	var out bytes.Buffer
	n := uint32(len(data))
	out.Write([]byte{byte(n >> 24), byte(n >> 16), byte(n >> 8), byte(n)})
	out.Write(chunkType)
	out.Write(data)
	crc := crc32.ChecksumIEEE(append(append([]byte{}, chunkType...), data...))
	out.Write([]byte{byte(crc >> 24), byte(crc >> 16), byte(crc >> 8), byte(crc)})
	return out.Bytes()
}

func pyAdler32(data []byte) uint32 {
	const mod uint32 = 65521
	var s1 uint32 = 1
	var s2 uint32 = 0
	for _, b := range data {
		s1 += uint32(b)
		if s1 >= mod {
			s1 -= mod
		}
		s2 += s1
		s2 %= mod
	}
	return ((s2 << 16) | s1) & 0xFFFFFFFF
}

func pyZlibDeflateStore(data []byte) []byte {
	out := make([]byte, 0, len(data)+16)
	out = append(out, 0x78, 0x01)
	n := len(data)
	pos := 0
	for pos < n {
		remain := n - pos
		chunkLen := remain
		if chunkLen > 65535 {
			chunkLen = 65535
		}
		final := byte(0)
		if pos+chunkLen >= n {
			final = 1
		}
		out = append(out, final)
		out = append(out, byte(chunkLen&0xFF), byte((chunkLen>>8)&0xFF))
		nlen := 0xFFFF ^ chunkLen
		out = append(out, byte(nlen&0xFF), byte((nlen>>8)&0xFF))
		out = append(out, data[pos:pos+chunkLen]...)
		pos += chunkLen
	}
	adler := pyAdler32(data)
	out = append(out, byte((adler>>24)&0xFF), byte((adler>>16)&0xFF), byte((adler>>8)&0xFF), byte(adler&0xFF))
	return out
}

func pyWriteRGBPNG(path any, width any, height any, pixels any) {
	w := pyToInt(width)
	h := pyToInt(height)
	raw := pyToBytes(pixels)
	expected := w * h * 3
	if len(raw) != expected {
		panic("pixels length mismatch")
	}

	scan := make([]byte, 0, h*(1+w*3))
	rowBytes := w * 3
	for y := 0; y < h; y++ {
		scan = append(scan, 0)
		start := y * rowBytes
		end := start + rowBytes
		scan = append(scan, raw[start:end]...)
	}

	idat := pyZlibDeflateStore(scan)

	ihdr := []byte{
		byte(uint32(w) >> 24), byte(uint32(w) >> 16), byte(uint32(w) >> 8), byte(uint32(w)),
		byte(uint32(h) >> 24), byte(uint32(h) >> 16), byte(uint32(h) >> 8), byte(uint32(h)),
		8, 2, 0, 0, 0,
	}

	var png bytes.Buffer
	png.Write([]byte{0x89, 'P', 'N', 'G', '\r', '\n', 0x1a, '\n'})
	png.Write(pyChunk([]byte("IHDR"), ihdr))
	png.Write(pyChunk([]byte("IDAT"), idat))
	png.Write(pyChunk([]byte("IEND"), []byte{}))

	_ = os.WriteFile(pyToString(path), png.Bytes(), 0o644)
}
