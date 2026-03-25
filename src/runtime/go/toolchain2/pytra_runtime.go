// pytra_runtime.go: toolchain2 Go emitter 用ランタイム。
//
// toolchain2/emit/go/ が生成するコードが呼び出す関数を提供する。
// 関数名は EAST3 の import 名 / runtime_call 名に一致させる。
//
// source: src/runtime/go/toolchain2/pytra_runtime.go

package main

import (
	"bytes"
	"compress/zlib"
	"encoding/binary"
	"fmt"
	"hash/crc32"
	"math"
	"math/rand"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"time"
)

// ---------------------------------------------------------------------------
// print / str
// ---------------------------------------------------------------------------

// __pytra_print emulates Python's print(): space-separated args + newline.
func __pytra_print(args ...interface{}) {
	parts := make([]string, len(args))
	for i, a := range args {
		parts[i] = fmt.Sprint(a)
	}
	fmt.Println(strings.Join(parts, " "))
}

// __pytra_str converts any value to string (Python str()).
func __pytra_str(v interface{}) string {
	return fmt.Sprint(v)
}

// ---------------------------------------------------------------------------
// time
// ---------------------------------------------------------------------------

var _pytra_perf_counter_start = time.Now()

// perf_counter returns seconds since an arbitrary epoch (Python time.perf_counter).
func perf_counter() float64 {
	return float64(time.Since(_pytra_perf_counter_start).Nanoseconds()) / 1e9
}

// Alias with __pytra_ prefix for emitter compatibility
func __pytra_perf_counter() float64 { return perf_counter() }

// ---------------------------------------------------------------------------
// pathlib
// ---------------------------------------------------------------------------

// Path is a minimal pathlib.Path equivalent.
func Path(s string) string { return s }
func __pytra_Path(s string) string { return s }

// __pytra_write_text writes content to a file (Python Path.write_text).
func __pytra_write_text(path string, content string) {
	dir := filepath.Dir(path)
	if dir != "" && dir != "." {
		os.MkdirAll(dir, 0755)
	}
	os.WriteFile(path, []byte(content), 0644)
}

// ---------------------------------------------------------------------------
// numeric / container helpers
// ---------------------------------------------------------------------------

// __pytra_len returns the length of a slice or string.
func __pytra_len(v interface{}) int64 {
	switch t := v.(type) {
	case string:
		return int64(len(t))
	case []int64:
		return int64(len(t))
	case []float64:
		return int64(len(t))
	case []string:
		return int64(len(t))
	case []byte:
		return int64(len(t))
	case []interface{}:
		return int64(len(t))
	default:
		return 0
	}
}

// __pytra_abs returns the absolute value.
func __pytra_abs(v int64) int64 {
	if v < 0 {
		return -v
	}
	return v
}

// __pytra_abs_float returns the absolute value of a float.
func __pytra_abs_float(v float64) float64 {
	if v < 0 {
		return -v
	}
	return v
}

// __pytra_min returns the minimum of two int64 values.
func __pytra_min(a int64, b int64) int64 {
	if a < b {
		return a
	}
	return b
}

// __pytra_max returns the maximum of two int64 values.
func __pytra_max(a int64, b int64) int64 {
	if a > b {
		return a
	}
	return b
}

// __pytra_floordiv performs Python-style floor division.
func __pytra_floordiv(a int64, b int64) int64 {
	q := a / b
	if (a^b) < 0 && q*b != a {
		q -= 1
	}
	return q
}

// __pytra_contains checks if needle is in haystack (Python `in` operator).
func __pytra_contains(haystack interface{}, needle interface{}) bool {
	switch h := haystack.(type) {
	case string:
		n, ok := needle.(string)
		if ok {
			return strings.Contains(h, n)
		}
	case []int64:
		n, ok := needle.(int64)
		if ok {
			for _, v := range h {
				if v == n {
					return true
				}
			}
		}
	case map[string]int64:
		n, ok := needle.(string)
		if ok {
			_, exists := h[n]
			return exists
		}
	}
	return false
}

// ---------------------------------------------------------------------------
// string methods
// ---------------------------------------------------------------------------

// __pytra_isdigit checks if a byte/string is a digit character.
func __pytra_isdigit(v interface{}) bool {
	switch t := v.(type) {
	case byte:
		return t >= '0' && t <= '9'
	case string:
		if len(t) == 0 {
			return false
		}
		for _, c := range t {
			if c < '0' || c > '9' {
				return false
			}
		}
		return true
	}
	return false
}

// __pytra_isalpha checks if a byte/string is alphabetic.
func __pytra_isalpha(v interface{}) bool {
	switch t := v.(type) {
	case byte:
		return (t >= 'a' && t <= 'z') || (t >= 'A' && t <= 'Z')
	case string:
		if len(t) == 0 {
			return false
		}
		for _, c := range t {
			if !((c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z')) {
				return false
			}
		}
		return true
	}
	return false
}

// __pytra_strip removes leading/trailing whitespace.
func __pytra_strip(s string) string {
	return strings.TrimSpace(s)
}

// __pytra_join joins strings with separator (Python str.join).
func __pytra_join(sep string, items []string) string {
	return strings.Join(items, sep)
}

// __pytra_replace replaces occurrences in a string.
func __pytra_replace(s string, old string, new_ string) string {
	return strings.ReplaceAll(s, old, new_)
}

// __pytra_split splits a string by separator.
func __pytra_split(s string, sep string) []string {
	return strings.Split(s, sep)
}

// __pytra_startswith checks string prefix.
func __pytra_startswith(s string, prefix string) bool {
	return strings.HasPrefix(s, prefix)
}

// __pytra_endswith checks string suffix.
func __pytra_endswith(s string, suffix string) bool {
	return strings.HasSuffix(s, suffix)
}

// __pytra_upper converts string to uppercase.
func __pytra_upper(s string) string {
	return strings.ToUpper(s)
}

// __pytra_lower converts string to lowercase.
func __pytra_lower(s string) string {
	return strings.ToLower(s)
}

// __pytra_find finds substring index (-1 if not found).
func __pytra_find(s string, sub string) int64 {
	return int64(strings.Index(s, sub))
}

// ---------------------------------------------------------------------------
// dict helpers
// ---------------------------------------------------------------------------

// __pytra_dict_get gets a value from map with default (for map[string]int64).
func __pytra_dict_get(m map[string]int64, key string, def_ int64) int64 {
	if v, ok := m[key]; ok {
		return v
	}
	return def_
}

// ---------------------------------------------------------------------------
// string/byte helpers
// ---------------------------------------------------------------------------

// __pytra_byte_eq compares a byte to a string character.
func __pytra_byte_eq(b byte, s string) bool {
	return len(s) == 1 && b == s[0]
}

// __pytra_byte_to_string converts a byte to a single-char string.
func __pytra_byte_to_string(b byte) string {
	return string([]byte{b})
}

// __pytra_str_to_int64 converts a string to int64 (Python int(str)).
func __pytra_str_to_int64(s string) int64 {
	v, _ := strconv.ParseInt(s, 10, 64)
	return v
}

// __pytra_ternary emulates Python's ternary (x if cond else y).
// Go doesn't have ternary, so we use a generic function.
func __pytra_ternary_int(cond bool, a int64, b int64) int64 {
	if cond { return a }
	return b
}
func __pytra_ternary_float(cond bool, a float64, b float64) float64 {
	if cond { return a }
	return b
}
func __pytra_ternary_str(cond bool, a string, b string) string {
	if cond { return a }
	return b
}

// __pytra_append_byte appends an int64 as byte to a byte slice.
func __pytra_append_byte(s []byte, v int64) []byte {
	return append(s, byte(v))
}

// __pytra_str_to_float64 converts a string to float64.
func __pytra_str_to_float64(s string) float64 {
	v, _ := strconv.ParseFloat(s, 64)
	return v
}

// ---------------------------------------------------------------------------
// math helpers
// ---------------------------------------------------------------------------

func _toF64(v interface{}) float64 {
	switch t := v.(type) {
	case float64: return t
	case int64: return float64(t)
	case int: return float64(t)
	case float32: return float64(t)
	default: return 0
	}
}
func __pytra_sqrt(x interface{}) float64  { return math.Sqrt(_toF64(x)) }
func __pytra_sin(x interface{}) float64   { return math.Sin(_toF64(x)) }
func __pytra_cos(x interface{}) float64   { return math.Cos(_toF64(x)) }
func __pytra_tan(x interface{}) float64   { return math.Tan(_toF64(x)) }
func __pytra_atan2(y, x interface{}) float64 { return math.Atan2(_toF64(y), _toF64(x)) }
func __pytra_floor(x interface{}) float64 { return math.Floor(_toF64(x)) }
func __pytra_ceil(x interface{}) float64  { return math.Ceil(_toF64(x)) }
func __pytra_pow(x, y interface{}) float64 { return math.Pow(_toF64(x), _toF64(y)) }
func __pytra_exp(x interface{}) float64   { return math.Exp(_toF64(x)) }
func __pytra_log(x interface{}) float64   { return math.Log(_toF64(x)) }
func __pytra_fabs(x interface{}) float64  { return math.Abs(_toF64(x)) }
func __pytra_pi() float64                 { return math.Pi }

// random
var _pytra_rng = rand.New(rand.NewSource(time.Now().UnixNano()))

func __pytra_random() float64         { return _pytra_rng.Float64() }
func __pytra_randint(a, b int64) int64 { return a + _pytra_rng.Int63n(b-a+1) }
func __pytra_seed(s int64)            { _pytra_rng = rand.New(rand.NewSource(s)) }

// ---------------------------------------------------------------------------
// PNG writer (minimal RGB)
// ---------------------------------------------------------------------------

func __pytra_write_rgb_png(path string, width int64, height int64, pixels []byte) {
	dir := filepath.Dir(path)
	if dir != "" && dir != "." {
		os.MkdirAll(dir, 0755)
	}
	w := int(width)
	h := int(height)
	var buf bytes.Buffer
	// PNG signature
	buf.Write([]byte{0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A})
	// IHDR
	ihdr := make([]byte, 13)
	binary.BigEndian.PutUint32(ihdr[0:4], uint32(w))
	binary.BigEndian.PutUint32(ihdr[4:8], uint32(h))
	ihdr[8] = 8  // bit depth
	ihdr[9] = 2  // color type RGB
	_writePNGChunk(&buf, "IHDR", ihdr)
	// IDAT
	var raw bytes.Buffer
	for y := 0; y < h; y++ {
		raw.WriteByte(0) // filter none
		row := pixels[y*w*3 : (y+1)*w*3]
		raw.Write(row)
	}
	var compressed bytes.Buffer
	zw, _ := zlib.NewWriterLevel(&compressed, zlib.BestSpeed)
	zw.Write(raw.Bytes())
	zw.Close()
	_writePNGChunk(&buf, "IDAT", compressed.Bytes())
	// IEND
	_writePNGChunk(&buf, "IEND", nil)
	os.WriteFile(path, buf.Bytes(), 0644)
}

func _writePNGChunk(buf *bytes.Buffer, chunkType string, data []byte) {
	length := make([]byte, 4)
	binary.BigEndian.PutUint32(length, uint32(len(data)))
	buf.Write(length)
	buf.WriteString(chunkType)
	if data != nil {
		buf.Write(data)
	}
	crc := crc32.NewIEEE()
	crc.Write([]byte(chunkType))
	if data != nil {
		crc.Write(data)
	}
	crcBytes := make([]byte, 4)
	binary.BigEndian.PutUint32(crcBytes, crc.Sum32())
	buf.Write(crcBytes)
}

// ---------------------------------------------------------------------------
// GIF writer (minimal)
// ---------------------------------------------------------------------------

func __pytra_grayscale_palette() []byte {
	pal := make([]byte, 256*3)
	for i := 0; i < 256; i++ {
		pal[i*3] = byte(i)
		pal[i*3+1] = byte(i)
		pal[i*3+2] = byte(i)
	}
	return pal
}

func __pytra_save_gif(path string, width int64, height int64, frames [][]byte, palette []byte, args ...int64) {
	delay_cs := int64(4)
	if len(args) > 0 {
		delay_cs = args[0]
	}
	dir := filepath.Dir(path)
	if dir != "" && dir != "." {
		os.MkdirAll(dir, 0755)
	}
	w := int(width)
	h := int(height)
	palSize := len(palette) / 3
	if palSize > 256 { palSize = 256 }

	var buf bytes.Buffer
	// GIF89a header
	buf.WriteString("GIF89a")
	_writeLE16(&buf, w)
	_writeLE16(&buf, h)
	// Global Color Table flag + color resolution + sort + size
	gctBits := 7 // 256 colors
	if palSize <= 128 { gctBits = 6 }
	if palSize <= 64 { gctBits = 5 }
	if palSize <= 32 { gctBits = 4 }
	if palSize <= 16 { gctBits = 3 }
	if palSize <= 8 { gctBits = 2 }
	if palSize <= 4 { gctBits = 1 }
	if palSize <= 2 { gctBits = 0 }
	buf.WriteByte(0x80 | byte(gctBits)<<4 | byte(gctBits))
	buf.WriteByte(0) // bg color
	buf.WriteByte(0) // aspect ratio
	// Global Color Table
	tableSize := 1 << (gctBits + 1)
	for i := 0; i < tableSize; i++ {
		if i < palSize {
			buf.Write(palette[i*3 : i*3+3])
		} else {
			buf.Write([]byte{0, 0, 0})
		}
	}
	// NETSCAPE extension for looping
	buf.Write([]byte{0x21, 0xFF, 0x0B})
	buf.WriteString("NETSCAPE2.0")
	buf.Write([]byte{0x03, 0x01, 0x00, 0x00, 0x00})

	minCodeSize := byte(gctBits + 1)
	if minCodeSize < 2 { minCodeSize = 2 }

	for _, frame := range frames {
		// Graphic Control Extension
		buf.Write([]byte{0x21, 0xF9, 0x04, 0x00})
		_writeLE16(&buf, int(delay_cs))
		buf.Write([]byte{0x00, 0x00})
		// Image Descriptor
		buf.WriteByte(0x2C)
		_writeLE16(&buf, 0) // left
		_writeLE16(&buf, 0) // top
		_writeLE16(&buf, w)
		_writeLE16(&buf, h)
		buf.WriteByte(0x00) // no local color table
		// LZW image data
		buf.WriteByte(minCodeSize)
		_writeLZW(&buf, frame, int(minCodeSize), w*h)
		buf.WriteByte(0x00) // block terminator
	}
	buf.WriteByte(0x3B) // trailer
	os.WriteFile(path, buf.Bytes(), 0644)
}

func _writeLE16(buf *bytes.Buffer, v int) {
	buf.WriteByte(byte(v & 0xFF))
	buf.WriteByte(byte((v >> 8) & 0xFF))
}

func _writeLZW(buf *bytes.Buffer, data []byte, minCodeSize int, pixelCount int) {
	clearCode := 1 << minCodeSize
	endCode := clearCode + 1

	var bitBuf uint32
	var bitCount uint
	var subBlock [255]byte
	subBlockLen := 0

	flushBits := func(code int, codeSize int) {
		bitBuf |= uint32(code) << bitCount
		bitCount += uint(codeSize)
		for bitCount >= 8 {
			subBlock[subBlockLen] = byte(bitBuf & 0xFF)
			subBlockLen++
			bitBuf >>= 8
			bitCount -= 8
			if subBlockLen == 255 {
				buf.WriteByte(byte(subBlockLen))
				buf.Write(subBlock[:subBlockLen])
				subBlockLen = 0
			}
		}
	}

	codeSize := minCodeSize + 1
	nextCode := endCode + 1
	maxCode := (1 << codeSize) - 1

	type entry struct{ prefix, suffix int }
	table := make(map[entry]int)

	flushBits(clearCode, codeSize)
	if len(data) == 0 {
		flushBits(endCode, codeSize)
	} else {
		prev := int(data[0])
		for i := 1; i < len(data) && i < pixelCount; i++ {
			cur := int(data[i])
			e := entry{prev, cur}
			if code, ok := table[e]; ok {
				prev = code
			} else {
				flushBits(prev, codeSize)
				if nextCode <= 4095 {
					table[e] = nextCode
					nextCode++
					if nextCode > maxCode+1 && codeSize < 12 {
						codeSize++
						maxCode = (1 << codeSize) - 1
					}
				} else {
					flushBits(clearCode, codeSize)
					table = make(map[entry]int)
					codeSize = minCodeSize + 1
					nextCode = endCode + 1
					maxCode = (1 << codeSize) - 1
				}
				prev = cur
			}
		}
		flushBits(prev, codeSize)
		flushBits(endCode, codeSize)
	}
	// Flush remaining bits
	if bitCount > 0 {
		subBlock[subBlockLen] = byte(bitBuf & 0xFF)
		subBlockLen++
	}
	if subBlockLen > 0 {
		buf.WriteByte(byte(subBlockLen))
		buf.Write(subBlock[:subBlockLen])
	}
}

// __pytra_int64 converts various types to int64.
func __pytra_int64(v interface{}) int64 {
	switch t := v.(type) {
	case int:
		return int64(t)
	case int64:
		return t
	case float64:
		return int64(t)
	case string:
		r, _ := strconv.ParseInt(t, 10, 64)
		return r
	}
	return 0
}
