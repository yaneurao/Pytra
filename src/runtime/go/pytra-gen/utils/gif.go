// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/utils/gif.py
// generated-by: tools/gen_image_runtime_from_canonical.py

package main

import "os"

func pyLzwEncode(data []byte, minCodeSize int) []byte {
	if len(data) == 0 {
		return []byte{}
	}
	clearCode := 1 << minCodeSize
	endCode := clearCode + 1
	codeSize := minCodeSize + 1
	out := []byte{}
	bitBuffer := 0
	bitCount := 0

	emit := func(code int) {
		bitBuffer |= (code << bitCount)
		bitCount += codeSize
		for bitCount >= 8 {
			out = append(out, byte(bitBuffer&0xff))
			bitBuffer >>= 8
			bitCount -= 8
		}
	}

	emit(clearCode)
	for _, v := range data {
		emit(int(v))
		emit(clearCode)
	}
	emit(endCode)
	if bitCount > 0 {
		out = append(out, byte(bitBuffer&0xff))
	}
	return out
}

func pyGrayscalePalette() any {
	p := make([]byte, 0, 256*3)
	for i := 0; i < 256; i++ {
		p = append(p, byte(i), byte(i), byte(i))
	}
	return p
}

func pySaveGIF(path any, width any, height any, frames any, palette any, delayCS any, loop any) {
	w := pyToInt(width)
	h := pyToInt(height)
	frameBytes := w * h
	pal := pyToBytes(palette)
	if len(pal) != 256*3 {
		panic("palette must be 256*3 bytes")
	}
	dcs := pyToInt(delayCS)
	lp := pyToInt(loop)

	frs := pyIter(frames)
	out := []byte{}
	out = append(out, []byte("GIF89a")...)
	out = append(out, byte(w), byte(w>>8), byte(h), byte(h>>8))
	out = append(out, 0xF7, 0, 0)
	out = append(out, pal...)

	out = append(out, 0x21, 0xFF, 0x0B)
	out = append(out, []byte("NETSCAPE2.0")...)
	out = append(out, 0x03, 0x01, byte(lp), byte(lp>>8), 0x00)

	for _, frAny := range frs {
		fr := pyToBytes(frAny)
		if len(fr) != frameBytes {
			panic("frame size mismatch")
		}
		out = append(out, 0x21, 0xF9, 0x04, 0x00, byte(dcs), byte(dcs>>8), 0x00, 0x00)
		out = append(out, 0x2C, 0, 0, 0, 0, byte(w), byte(w>>8), byte(h), byte(h>>8), 0x00)
		out = append(out, 0x08)
		compressed := pyLzwEncode(fr, 8)
		pos := 0
		for pos < len(compressed) {
			ln := len(compressed) - pos
			if ln > 255 {
				ln = 255
			}
			out = append(out, byte(ln))
			out = append(out, compressed[pos:pos+ln]...)
			pos += ln
		}
		out = append(out, 0x00)
	}
	out = append(out, 0x3B)
	_ = os.WriteFile(pyToString(path), out, 0o644)
}
