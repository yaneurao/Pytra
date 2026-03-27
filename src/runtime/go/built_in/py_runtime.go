// py_runtime.go: Python built-in function equivalents.
// Only contains Python built-in functions. pytra.std.* and pytra.utils.* are
// provided by native files (std/) or pipeline-generated code (utils/).
// See docs/ja/spec/spec-emitter-guide.md §6.
package main

import (
	gofmt "fmt"
	"io"
	"os"
	goreflect "reflect"
	"strconv"
	"strings"
)

func py_print(args ...any) {
	parts := make([]string, len(args))
	for i, a := range args {
		parts[i] = py_str(a)
	}
	gofmt.Println(strings.Join(parts, " "))
}

func py_format_float64(v float64) string {
	text := strconv.FormatFloat(v, 'g', -1, 64)
	if !strings.ContainsAny(text, ".eE") {
		return text + ".0"
	}
	return text
}

func py_format_sequence(v any) string {
	rv := goreflect.ValueOf(v)
	if !rv.IsValid() {
		return "[]"
	}
	if rv.Kind() != goreflect.Slice && rv.Kind() != goreflect.Array {
		return gofmt.Sprint(v)
	}
	if rv.Kind() == goreflect.Slice && rv.Type().Elem().Kind() == goreflect.Uint8 {
		return gofmt.Sprint(v)
	}
	parts := make([]string, rv.Len())
	for i := 0; i < rv.Len(); i++ {
		parts[i] = py_str(rv.Index(i).Interface())
	}
	return "[" + strings.Join(parts, ", ") + "]"
}

func py_type_name(v any) string {
	if v == nil {
		return "NoneType"
	}
	switch v.(type) {
	case bool:
		return "bool"
	case int, int8, int16, int32, int64, uint, uint8, uint16, uint32, uint64:
		return "int"
	case float32, float64:
		return "float"
	case string:
		return "str"
	}
	rv := goreflect.ValueOf(v)
	for rv.IsValid() && (rv.Kind() == goreflect.Interface || rv.Kind() == goreflect.Pointer) {
		if rv.IsNil() {
			return "NoneType"
		}
		rv = rv.Elem()
	}
	if !rv.IsValid() {
		return "NoneType"
	}
	if name := rv.Type().Name(); name != "" {
		return name
	}
	switch rv.Kind() {
	case goreflect.Slice, goreflect.Array:
		return "list"
	case goreflect.Map:
		return "dict"
	}
	return rv.Kind().String()
}

func py_str(v any) string {
	if v == nil {
		return "None"
	}
	if s, ok := v.(interface{ __str__() string }); ok {
		return s.__str__()
	}
	rv := goreflect.ValueOf(v)
	for rv.IsValid() && (rv.Kind() == goreflect.Interface || rv.Kind() == goreflect.Pointer) {
		if rv.IsNil() {
			return "None"
		}
		rv = rv.Elem()
		v = rv.Interface()
	}
	switch t := v.(type) {
	case bool:
		if t {
			return "True"
		}
		return "False"
	case float32:
		return py_format_float64(float64(t))
	case float64:
		return py_format_float64(t)
	}
	if rv.Kind() == goreflect.Slice || rv.Kind() == goreflect.Array {
		return py_format_sequence(v)
	}
	return gofmt.Sprint(v)
}
func py_to_string(v any) string { return py_str(v) }

type PyFile struct {
	file *os.File
}

type SystemExit int64

func py_open(path string, mode string, _kwargs ...any) *PyFile {
	var flag int
	switch mode {
	case "r", "rb":
		flag = os.O_RDONLY
	case "w", "wb":
		flag = os.O_WRONLY | os.O_CREATE | os.O_TRUNC
	default:
		panic("unsupported open mode: " + mode)
	}
	f, err := os.OpenFile(path, flag, 0644)
	if err != nil {
		panic(err)
	}
	return &PyFile{file: f}
}

func (f *PyFile) read() string {
	data, err := io.ReadAll(f.file)
	if err != nil {
		panic(err)
	}
	return string(data)
}

func (f *PyFile) write(data any) int64 {
	switch t := data.(type) {
	case string:
		n, err := f.file.WriteString(t)
		if err != nil {
			panic(err)
		}
		return int64(n)
	case []byte:
		n, err := f.file.Write(t)
		if err != nil {
			panic(err)
		}
		return int64(n)
	default:
		n, err := f.file.WriteString(py_str(t))
		if err != nil {
			panic(err)
		}
		return int64(n)
	}
}

func (f *PyFile) close() {
	if err := f.file.Close(); err != nil {
		panic(err)
	}
}

func py_len(v any) int64 {
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
	case []any:
		return int64(len(t))
	default:
		return 0
	}
}

func py_pop(m map[string]any, key string, defaultValue any) any {
	if m == nil {
		return defaultValue
	}
	if value, ok := m[key]; ok {
		delete(m, key)
		return value
	}
	return defaultValue
}

func py_abs(v int64) int64 {
	if v < 0 {
		return -v
	}
	return v
}
func py_abs_float(v float64) float64 {
	if v < 0 {
		return -v
	}
	return v
}
func py_min_int(a, b int64) int64 {
	if a < b {
		return a
	}
	return b
}
func py_max_int(a, b int64) int64 {
	if a > b {
		return a
	}
	return b
}
func py_min_float(a, b float64) float64 {
	if a < b {
		return a
	}
	return b
}
func py_max_float(a, b float64) float64 {
	if a > b {
		return a
	}
	return b
}

type pyNumber interface {
	~int | ~int8 | ~int16 | ~int32 | ~int64 |
		~uint8 | ~uint16 | ~uint32 | ~uint64 |
		~float32 | ~float64
}

func py_sum[T pyNumber](values []T) T {
	var acc T
	for _, value := range values {
		acc += value
	}
	return acc
}

func py_zip[A any, B any](lhs []A, rhs []B) [][]any {
	n := len(lhs)
	if len(rhs) < n {
		n = len(rhs)
	}
	out := make([][]any, 0, n)
	for i := 0; i < n; i++ {
		out = append(out, []any{lhs[i], rhs[i]})
	}
	return out
}

func py_floordiv(a, b int64) int64 {
	q := a / b
	if (a^b) < 0 && q*b != a {
		q -= 1
	}
	return q
}

func py_truthy(v any) bool {
	if v == nil {
		return false
	}
	rv := goreflect.ValueOf(v)
	switch rv.Kind() {
	case goreflect.Bool:
		return rv.Bool()
	case goreflect.String, goreflect.Array, goreflect.Slice, goreflect.Map:
		return rv.Len() != 0
	case goreflect.Int, goreflect.Int8, goreflect.Int16, goreflect.Int32, goreflect.Int64:
		return rv.Int() != 0
	case goreflect.Uint, goreflect.Uint8, goreflect.Uint16, goreflect.Uint32, goreflect.Uint64, goreflect.Uintptr:
		return rv.Uint() != 0
	case goreflect.Float32, goreflect.Float64:
		return rv.Float() != 0
	case goreflect.Interface, goreflect.Pointer:
		return !rv.IsNil()
	default:
		return true
	}
}

func py_bool(v any) bool { return py_truthy(v) }

func py_eq(a any, b any) bool {
	if goreflect.DeepEqual(a, b) {
		return true
	}
	_, a_is_string := a.(string)
	_, b_is_string := b.(string)
	if a_is_string != b_is_string {
		return false
	}
	av := goreflect.ValueOf(a)
	bv := goreflect.ValueOf(b)
	if !av.IsValid() || !bv.IsValid() {
		return !av.IsValid() && !bv.IsValid()
	}
	if av.Type().ConvertibleTo(bv.Type()) {
		return goreflect.DeepEqual(av.Convert(bv.Type()).Interface(), b)
	}
	if bv.Type().ConvertibleTo(av.Type()) {
		return goreflect.DeepEqual(a, bv.Convert(av.Type()).Interface())
	}
	return false
}

func py_contains(haystack any, needle any) bool {
	switch h := haystack.(type) {
	case string:
		switch n := needle.(type) {
		case string:
			return strings.Contains(h, n)
		case byte:
			return strings.Contains(h, string([]byte{n}))
		}
	}
	rv := goreflect.ValueOf(haystack)
	if !rv.IsValid() {
		return false
	}
	switch rv.Kind() {
	case goreflect.Array, goreflect.Slice:
		for i := 0; i < rv.Len(); i++ {
			if py_eq(rv.Index(i).Interface(), needle) {
				return true
			}
		}
	case goreflect.Map:
		kv := goreflect.ValueOf(needle)
		if !kv.IsValid() {
			return false
		}
		if kv.Type().AssignableTo(rv.Type().Key()) {
			return rv.MapIndex(kv).IsValid()
		}
		if kv.Type().ConvertibleTo(rv.Type().Key()) {
			return rv.MapIndex(kv.Convert(rv.Type().Key())).IsValid()
		}
	}
	return false
}

func py_is_none(v any) bool {
	if v == nil {
		return true
	}
	rv := goreflect.ValueOf(v)
	if !rv.IsValid() {
		return true
	}
	if rv.Kind() == goreflect.Interface || rv.Kind() == goreflect.Pointer {
		return rv.IsNil()
	}
	return false
}

func py_is_bool_type(v any) bool {
	rv := goreflect.ValueOf(v)
	return rv.IsValid() && rv.Kind() == goreflect.Bool
}

func py_is_int(v any) bool {
	rv := goreflect.ValueOf(v)
	if !rv.IsValid() {
		return false
	}
	switch rv.Kind() {
	case goreflect.Int, goreflect.Int8, goreflect.Int16, goreflect.Int32, goreflect.Int64:
		return true
	case goreflect.Uint, goreflect.Uint8, goreflect.Uint16, goreflect.Uint32, goreflect.Uint64, goreflect.Uintptr:
		return true
	default:
		return false
	}
}

func py_is_exact_int8(v any) bool    { return goreflect.TypeOf(v) == goreflect.TypeOf(int8(0)) }
func py_is_exact_uint8(v any) bool   { return goreflect.TypeOf(v) == goreflect.TypeOf(uint8(0)) }
func py_is_exact_int16(v any) bool   { return goreflect.TypeOf(v) == goreflect.TypeOf(int16(0)) }
func py_is_exact_uint16(v any) bool  { return goreflect.TypeOf(v) == goreflect.TypeOf(uint16(0)) }
func py_is_exact_int32(v any) bool   { return goreflect.TypeOf(v) == goreflect.TypeOf(int32(0)) }
func py_is_exact_uint32(v any) bool  { return goreflect.TypeOf(v) == goreflect.TypeOf(uint32(0)) }
func py_is_exact_int64(v any) bool   { return goreflect.TypeOf(v) == goreflect.TypeOf(int64(0)) }
func py_is_exact_uint64(v any) bool  { return goreflect.TypeOf(v) == goreflect.TypeOf(uint64(0)) }
func py_is_exact_float32(v any) bool { return goreflect.TypeOf(v) == goreflect.TypeOf(float32(0)) }
func py_is_exact_float64(v any) bool { return goreflect.TypeOf(v) == goreflect.TypeOf(float64(0)) }

func py_is_float(v any) bool {
	rv := goreflect.ValueOf(v)
	if !rv.IsValid() {
		return false
	}
	return rv.Kind() == goreflect.Float32 || rv.Kind() == goreflect.Float64
}

func py_is_str(v any) bool {
	rv := goreflect.ValueOf(v)
	return rv.IsValid() && rv.Kind() == goreflect.String
}

func py_is_list(v any) bool {
	rv := goreflect.ValueOf(v)
	if !rv.IsValid() {
		return false
	}
	return rv.Kind() == goreflect.Slice || rv.Kind() == goreflect.Array
}

func py_is_dict(v any) bool {
	rv := goreflect.ValueOf(v)
	return rv.IsValid() && rv.Kind() == goreflect.Map
}

func py_ternary_int(cond bool, a, b int64) int64 {
	if cond {
		return a
	}
	return b
}
func py_ternary_float(cond bool, a, b float64) float64 {
	if cond {
		return a
	}
	return b
}
func py_ternary_str(cond bool, a, b string) string {
	if cond {
		return a
	}
	return b
}
func py_append_byte(s []byte, v any) []byte {
	switch t := v.(type) {
	case byte:
		return append(s, t)
	case int64:
		return append(s, byte(t))
	case int:
		return append(s, byte(t))
	default:
		return s
	}
}

func py_list_pop(seq any, args ...int64) any {
	rv := goreflect.ValueOf(seq)
	if !rv.IsValid() || rv.Kind() != goreflect.Pointer {
		panic("py_list_pop expects pointer to slice")
	}
	sv := rv.Elem()
	if sv.Kind() != goreflect.Slice {
		panic("py_list_pop expects pointer to slice")
	}
	n := sv.Len()
	idx := n - 1
	if len(args) > 0 {
		idx = int(args[0])
		if idx < 0 {
			idx += n
		}
	}
	if idx < 0 || idx >= n {
		panic("pop index out of range")
	}
	val := sv.Index(idx).Interface()
	newSlice := goreflect.AppendSlice(sv.Slice(0, idx), sv.Slice(idx+1, n))
	sv.Set(newSlice)
	return val
}

func py_repeat_int64(val, count int64) []int64 {
	s := make([]int64, count)
	for i := int64(0); i < count; i++ {
		s[i] = val
	}
	return s
}

func py_repeat_slice[T any](items []T, count int64) []T {
	if count <= 0 || len(items) == 0 {
		return []T{}
	}
	out := make([]T, 0, len(items)*int(count))
	for i := int64(0); i < count; i++ {
		out = append(out, items...)
	}
	return out
}

func py_concat_slice[T any](left []T, right []T) []T {
	out := make([]T, 0, len(left)+len(right))
	out = append(out, left...)
	out = append(out, right...)
	return out
}

func py_index[T comparable](items []T, needle T) int64 {
	for i, item := range items {
		if item == needle {
			return int64(i)
		}
	}
	panic("value is not in list")
}

func py_repeat_string(s string, count int64) string {
	if count <= 0 {
		return ""
	}
	return strings.Repeat(s, int(count))
}

// String methods
func py_str_isdigit(v any) bool {
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
func py_str_isalpha(v any) bool {
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
func py_str_isalnum(v any) bool {
	switch t := v.(type) {
	case byte:
		return (t >= '0' && t <= '9') || (t >= 'a' && t <= 'z') || (t >= 'A' && t <= 'Z')
	case string:
		if len(t) == 0 {
			return false
		}
		for _, c := range t {
			if !((c >= '0' && c <= '9') || (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z')) {
				return false
			}
		}
		return true
	}
	return false
}
func py_str_isspace(v any) bool {
	switch t := v.(type) {
	case byte:
		return t == ' ' || t == '\t' || t == '\r' || t == '\n'
	case string:
		if len(t) == 0 {
			return false
		}
		for _, c := range t {
			if c != ' ' && c != '\t' && c != '\r' && c != '\n' {
				return false
			}
		}
		return true
	}
	return false
}
func py_str_strip(s string, chars ...string) string {
	if len(chars) > 0 {
		return strings.Trim(s, chars[0])
	}
	return strings.TrimSpace(s)
}
func py_str_lstrip(s string, chars ...string) string {
	if len(chars) > 0 {
		return strings.TrimLeft(s, chars[0])
	}
	return strings.TrimLeft(s, " \t\r\n")
}
func py_str_rstrip(s string, chars ...string) string {
	if len(chars) > 0 {
		return strings.TrimRight(s, chars[0])
	}
	return strings.TrimRight(s, " \t\r\n")
}
func py_str_join(sep string, items []string) string { return strings.Join(items, sep) }
func py_str_replace(s, old, new_ string) string     { return strings.ReplaceAll(s, old, new_) }
func py_str_split(s, sep string) []string           { return strings.Split(s, sep) }
func py_str_startswith(s, prefix string) bool       { return strings.HasPrefix(s, prefix) }
func py_str_endswith(s, suffix string) bool         { return strings.HasSuffix(s, suffix) }
func py_str_upper(s string) string                  { return strings.ToUpper(s) }
func py_str_lower(s string) string                  { return strings.ToLower(s) }
func py_str_find(s, sub string) int64               { return int64(strings.Index(s, sub)) }
func py_str_rfind(s, sub string) int64              { return int64(strings.LastIndex(s, sub)) }
func py_str_index(s, sub string) int64 {
	idx := strings.Index(s, sub)
	if idx < 0 {
		panic("substring not found")
	}
	return int64(idx)
}
func py_list_index(seq any, needle any) int64 {
	rv := goreflect.ValueOf(seq)
	if !rv.IsValid() || (rv.Kind() != goreflect.Slice && rv.Kind() != goreflect.Array) {
		panic("value is not a list")
	}
	for i := 0; i < rv.Len(); i++ {
		if py_eq(rv.Index(i).Interface(), needle) {
			return int64(i)
		}
	}
	panic("value not in list")
}
func py_strip(s string) string            { return py_str_strip(s) }
func py_rstrip(s string) string           { return py_str_rstrip(s) }
func py_find(s, sub string) int64         { return py_str_find(s, sub) }
func py_rfind(s, sub string) int64        { return py_str_rfind(s, sub) }
func py_startswith(s, prefix string) bool { return py_str_startswith(s, prefix) }
func py_endswith(s, suffix string) bool   { return py_str_endswith(s, suffix) }

func py_enumerate[T any](seq []T, start ...int64) [][]any {
	idx := int64(0)
	if len(start) > 0 {
		idx = start[0]
	}
	out := make([][]any, 0, len(seq))
	for _, item := range seq {
		out = append(out, []any{idx, item})
		idx += 1
	}
	return out
}

func py_reversed[T any](seq []T) []T {
	out := make([]T, len(seq))
	for i := range seq {
		out[len(seq)-1-i] = seq[i]
	}
	return out
}

func py_discard[K comparable](s map[K]struct{}, key K) {
	delete(s, key)
}

func py_remove[K comparable](s map[K]struct{}, key K) {
	if _, ok := s[key]; !ok {
		panic("KeyError")
	}
	delete(s, key)
}

// Dict
func py_dict_get(m any, key any, def_ any) any {
	mv := goreflect.ValueOf(m)
	if !mv.IsValid() || mv.Kind() != goreflect.Map {
		return def_
	}
	kv := goreflect.ValueOf(key)
	if !kv.IsValid() {
		return def_
	}
	if kv.Type().AssignableTo(mv.Type().Key()) {
		v := mv.MapIndex(kv)
		if v.IsValid() {
			return v.Interface()
		}
		return def_
	}
	if kv.Type().ConvertibleTo(mv.Type().Key()) {
		v := mv.MapIndex(kv.Convert(mv.Type().Key()))
		if v.IsValid() {
			return v.Interface()
		}
	}
	return def_
}

func py_items(m any) [][]any {
	mv := goreflect.ValueOf(m)
	if !mv.IsValid() || mv.Kind() != goreflect.Map {
		return [][]any{}
	}
	keys := mv.MapKeys()
	out := make([][]any, 0, len(keys))
	for _, key := range keys {
		value := mv.MapIndex(key)
		out = append(out, []any{key.Interface(), value.Interface()})
	}
	return out
}

func py_dict_keys(m any) []string {
	mv := goreflect.ValueOf(m)
	if !mv.IsValid() || mv.Kind() != goreflect.Map {
		return []string{}
	}
	keys := mv.MapKeys()
	out := make([]string, 0, len(keys))
	for _, key := range keys {
		if key.Kind() == goreflect.String {
			out = append(out, key.String())
		}
	}
	return out
}

func py_dict_values(m any) []any {
	mv := goreflect.ValueOf(m)
	if !mv.IsValid() || mv.Kind() != goreflect.Map {
		return []any{}
	}
	keys := mv.MapKeys()
	out := make([]any, 0, len(keys))
	for _, key := range keys {
		value := mv.MapIndex(key)
		out = append(out, value.Interface())
	}
	return out
}

func py_iter(v any) []any {
	rv := goreflect.ValueOf(v)
	if !rv.IsValid() {
		return []any{}
	}
	for rv.Kind() == goreflect.Interface || rv.Kind() == goreflect.Pointer {
		if rv.IsNil() {
			return []any{}
		}
		rv = rv.Elem()
	}
	switch rv.Kind() {
	case goreflect.Slice, goreflect.Array:
		out := make([]any, rv.Len())
		for i := 0; i < rv.Len(); i++ {
			out[i] = rv.Index(i).Interface()
		}
		return out
	case goreflect.Map:
		keys := rv.MapKeys()
		out := make([]any, 0, len(keys))
		for _, key := range keys {
			out = append(out, key.Interface())
		}
		return out
	case goreflect.String:
		text := rv.String()
		out := make([]any, 0, len(text))
		for _, ch := range text {
			out = append(out, string(ch))
		}
		return out
	default:
		return []any{}
	}
}

type pySetSource[T comparable] interface {
	~[]T | ~map[T]struct{}
}

func py_set[T comparable, S pySetSource[T]](values S) map[T]struct{} {
	out := map[T]struct{}{}
	switch src := any(values).(type) {
	case []T:
		for _, value := range src {
			out[value] = struct{}{}
		}
	case map[T]struct{}:
		for value := range src {
			out[value] = struct{}{}
		}
	}
	return out
}

func py_set_str(values any) map[string]struct{} {
	out := map[string]struct{}{}
	switch t := values.(type) {
	case []string:
		for _, value := range t {
			out[value] = struct{}{}
		}
	case map[string]struct{}:
		for value := range t {
			out[value] = struct{}{}
		}
	case map[any]struct{}:
		for raw := range t {
			if value, ok := raw.(string); ok {
				out[value] = struct{}{}
			}
		}
	}
	return out
}

func py_set_update_str(dst map[string]struct{}, values any) map[string]struct{} {
	if dst == nil {
		dst = map[string]struct{}{}
	}
	switch t := values.(type) {
	case []string:
		for _, value := range t {
			dst[value] = struct{}{}
		}
	case map[string]struct{}:
		for value := range t {
			dst[value] = struct{}{}
		}
	case map[any]struct{}:
		for raw := range t {
			if value, ok := raw.(string); ok {
				dst[value] = struct{}{}
			}
		}
	}
	return dst
}

func py_set_union_str(left map[string]struct{}, right map[string]struct{}) map[string]struct{} {
	out := map[string]struct{}{}
	for value := range left {
		out[value] = struct{}{}
	}
	for value := range right {
		out[value] = struct{}{}
	}
	return out
}

func py_to_map_string_any(v any) map[string]any {
	if v == nil {
		return nil
	}
	if m, ok := v.(map[string]any); ok {
		return m
	}
	mv := goreflect.ValueOf(v)
	if !mv.IsValid() || mv.Kind() != goreflect.Map || mv.Type().Key().Kind() != goreflect.String {
		panic("py_to_map_string_any: expected map with string keys")
	}
	out := map[string]any{}
	iter := mv.MapRange()
	for iter.Next() {
		out[iter.Key().String()] = iter.Value().Interface()
	}
	return out
}

// Type conversions
func py_byte_eq(b byte, s string) bool { return len(s) == 1 && b == s[0] }
func py_byte_to_string(b byte) string  { return string([]byte{b}) }
func py_ord(s string) int64 {
	if s == "" {
		return 0
	}
	r := []rune(s)
	if len(r) == 0 {
		return 0
	}
	return int64(r[0])
}
func py_chr(v int64) string              { return string(rune(v)) }
func py_str_to_int64(s string) int64     { v, _ := strconv.ParseInt(s, 10, 64); return v }
func py_str_to_float64(s string) float64 { v, _ := strconv.ParseFloat(s, 64); return v }

func _toF64(v any) float64 {
	switch t := v.(type) {
	case float64:
		return t
	case int64:
		return float64(t)
	case int:
		return float64(t)
	case float32:
		return float64(t)
	default:
		rv := goreflect.ValueOf(v)
		if !rv.IsValid() {
			return 0
		}
		switch rv.Kind() {
		case goreflect.Int, goreflect.Int8, goreflect.Int16, goreflect.Int32, goreflect.Int64:
			return float64(rv.Int())
		case goreflect.Uint, goreflect.Uint8, goreflect.Uint16, goreflect.Uint32, goreflect.Uint64, goreflect.Uintptr:
			return float64(rv.Uint())
		case goreflect.Float32, goreflect.Float64:
			return rv.Float()
		default:
			return 0
		}
	}
}
func py_to_int64(v any) int64 {
	switch t := v.(type) {
	case int64:
		return t
	case int:
		return int64(t)
	case float64:
		return int64(t)
	default:
		rv := goreflect.ValueOf(v)
		if !rv.IsValid() {
			return 0
		}
		switch rv.Kind() {
		case goreflect.Int, goreflect.Int8, goreflect.Int16, goreflect.Int32, goreflect.Int64:
			return rv.Int()
		case goreflect.Uint, goreflect.Uint8, goreflect.Uint16, goreflect.Uint32, goreflect.Uint64, goreflect.Uintptr:
			return int64(rv.Uint())
		case goreflect.Float32, goreflect.Float64:
			return int64(rv.Float())
		default:
			return 0
		}
	}
}
func py_to_float64(v any) float64 { return _toF64(v) }
func py_int64(v any) int64 {
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
