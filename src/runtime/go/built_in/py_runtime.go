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
	"sort"
	"strconv"
	"strings"
)

type PyList[T any] struct {
	items []T
}

func (*PyList[T]) __pytra_is_list() {}
func (p *PyList[T]) __len__() int64 {
	if p == nil {
		return 0
	}
	return int64(len(p.items))
}

type pyListView interface {
	pyListLen() int
	pyListItemAny(i int) any
}

type pyDictView interface {
	pyIsDictView()
}

type pyDictAccessor interface {
	pyDictItemsAny() any
}

type pySetAccessor interface {
	pySetItemsAny() any
}

func NewPyList[T any]() *PyList[T] {
	return &PyList[T]{items: []T{}}
}

func PyListFromSlice[T any](items []T) *PyList[T] {
	out := make([]T, len(items))
	copy(out, items)
	return &PyList[T]{items: out}
}

type PyTuple []any

func py_tuple_any(values ...any) PyTuple {
	return PyTuple(values)
}

func py_tuple_key(value any) string {
	return gofmt.Sprintf("%#v", value)
}

func py_list_any(items any) *PyList[any] {
	if items == nil {
		return NewPyList[any]()
	}
	if direct, ok := items.(*PyList[any]); ok {
		return direct
	}
	if view, ok := items.(pyListView); ok {
		out := NewPyList[any]()
		out.items = make([]any, view.pyListLen())
		for i := 0; i < view.pyListLen(); i++ {
			out.items[i] = view.pyListItemAny(i)
		}
		return out
	}
	out := NewPyList[any]()
	rv := goreflect.ValueOf(items)
	for rv.IsValid() && rv.Kind() == goreflect.Interface {
		rv = rv.Elem()
	}
	if rv.IsValid() && rv.Kind() == goreflect.Pointer && !rv.IsNil() {
		elem := rv.Elem()
		if elem.IsValid() && elem.Kind() == goreflect.Struct {
			itemsField := elem.FieldByName("items")
			if itemsField.IsValid() && itemsField.CanInterface() {
				rv = itemsField
			}
		}
	}
	if !rv.IsValid() || (rv.Kind() != goreflect.Slice && rv.Kind() != goreflect.Array) {
		return out
	}
	out.items = make([]any, rv.Len())
	for i := 0; i < rv.Len(); i++ {
		out.items[i] = rv.Index(i).Interface()
	}
	return out
}

func py_to_list_typed[T any](items any) *PyList[T] {
	if items == nil {
		return nil
	}
	if direct, ok := items.(*PyList[T]); ok {
		return direct
	}
	rv := goreflect.ValueOf(items)
	for rv.IsValid() && rv.Kind() == goreflect.Interface {
		rv = rv.Elem()
	}
	if !rv.IsValid() {
		return nil
	}
	if rv.Kind() == goreflect.Pointer && !rv.IsNil() {
		elem := rv.Elem()
		if elem.IsValid() && elem.Kind() == goreflect.Struct {
			itemsField := elem.FieldByName("items")
			if itemsField.IsValid() && (itemsField.Kind() == goreflect.Slice || itemsField.Kind() == goreflect.Array) {
				rv = itemsField
			}
		}
	}
	if rv.Kind() != goreflect.Slice && rv.Kind() != goreflect.Array {
		return NewPyList[T]()
	}
	out := make([]T, rv.Len())
	var zero T
	targetType := goreflect.TypeOf(zero)
	if targetType == nil {
		for i := 0; i < rv.Len(); i++ {
			out[i] = rv.Index(i).Interface().(T)
		}
		return &PyList[T]{items: out}
	}
	for i := 0; i < rv.Len(); i++ {
		item := rv.Index(i)
		if item.IsValid() && item.Type().AssignableTo(targetType) {
			out[i] = item.Interface().(T)
			continue
		}
		if item.IsValid() && item.Type().ConvertibleTo(targetType) {
			out[i] = item.Convert(targetType).Interface().(T)
			continue
		}
		out[i] = item.Interface().(T)
	}
	return &PyList[T]{items: out}
}

func py_dict_string_any(items any) *PyDict[string, any] {
	if items == nil {
		return NewPyDict[string, any]()
	}
	if direct, ok := items.(*PyDict[string, any]); ok {
		return direct
	}
	out := NewPyDict[string, any]()
	rv := goreflect.ValueOf(items)
	for rv.IsValid() && rv.Kind() == goreflect.Interface {
		rv = rv.Elem()
	}
	if rv.IsValid() && rv.Kind() == goreflect.Pointer && !rv.IsNil() {
		elem := rv.Elem()
		if elem.IsValid() && elem.Kind() == goreflect.Struct {
			itemsField := elem.FieldByName("items")
			if itemsField.IsValid() && itemsField.Kind() == goreflect.Map {
				rv = itemsField
			}
		}
	}
	if !rv.IsValid() || rv.Kind() != goreflect.Map {
		return out
	}
	iter := rv.MapRange()
	for iter.Next() {
		out.items[py_str(iter.Key().Interface())] = iter.Value().Interface()
	}
	return out
}

func py_extend[T any](dst *PyList[T], src *PyList[T]) {
	if dst == nil || src == nil {
		return
	}
	dst.items = append(dst.items, src.items...)
}

func py_list_insert[T any](list *PyList[T], index int64, value T) {
	if list == nil {
		return
	}
	if index < 0 {
		index = 0
	}
	if index > int64(len(list.items)) {
		index = int64(len(list.items))
	}
	i := int(index)
	list.items = append(list.items, value)
	copy(list.items[i+1:], list.items[i:])
	list.items[i] = value
}

func (p *PyList[T]) pyListLen() int {
	if p == nil {
		return 0
	}
	return len(p.items)
}

func (p *PyList[T]) pyListItemAny(i int) any {
	return p.items[i]
}

func (p *PyList[T]) clear_items() {
	if p == nil {
		return
	}
	p.items = p.items[:0]
}

func (p *PyList[T]) reverse_items() {
	if p == nil {
		return
	}
	for i, j := 0, len(p.items)-1; i < j; i, j = i+1, j-1 {
		p.items[i], p.items[j] = p.items[j], p.items[i]
	}
}

func (p *PyList[T]) sort_items() {
	if p == nil {
		return
	}
	sort.Slice(p.items, func(i, j int) bool {
		return py_less_any(p.items[i], p.items[j])
	})
}

func (p *PyList[T]) __str__() string {
	if p == nil {
		return "[]"
	}
	return py_format_sequence_repr(p.items)
}

type PyDict[K comparable, V any] struct {
	items map[K]V
}

func (*PyDict[K, V]) __pytra_is_dict() {}
func (d *PyDict[K, V]) __len__() int64 {
	if d == nil {
		return 0
	}
	return int64(len(d.items))
}
func (d *PyDict[K, V]) pyDictItemsAny() any { return d.items }
func (d *PyDict[K, V]) get(key K, fallback V) V {
	if d == nil {
		return fallback
	}
	if value, ok := d.items[key]; ok {
		return value
	}
	return fallback
}
func (d *PyDict[K, V]) __str__() string {
	if d == nil {
		return "{}"
	}
	return py_format_mapping_repr(d.items)
}

func NewPyDict[K comparable, V any]() *PyDict[K, V] {
	return &PyDict[K, V]{items: map[K]V{}}
}

func PyDictFromMap[K comparable, V any](items any) *PyDict[K, V] {
	if direct, ok := items.(*PyDict[K, V]); ok {
		return direct
	}
	out := map[K]V{}
	if typed, ok := items.(map[K]V); ok {
		for k, v := range typed {
			out[k] = v
		}
	}
	return &PyDict[K, V]{items: out}
}

// pyIsDictView marks *PyDict[K,V] as a dict type for py_is_dict checks.
func (d *PyDict[K, V]) pyIsDictView() {}

func (d *PyDict[K, V]) clear_items() {
	if d == nil {
		return
	}
	clear(d.items)
}

// pyMapStringAny converts a PyDict with string-compatible keys to map[string]any.
// Used by py_to_map_string_any to handle *PyDict[string, V] without external reflection.
func (d *PyDict[K, V]) pyMapStringAny() map[string]any {
	rv := goreflect.ValueOf(d.items)
	if !rv.IsValid() || rv.Kind() != goreflect.Map || rv.Type().Key().Kind() != goreflect.String {
		return nil
	}
	out := map[string]any{}
	iter := rv.MapRange()
	for iter.Next() {
		out[iter.Key().String()] = iter.Value().Interface()
	}
	return out
}

type PySet[T comparable] struct {
	items map[T]struct{}
}

func (*PySet[T]) __pytra_is_set() {}
func (s *PySet[T]) __len__() int64 {
	if s == nil {
		return 0
	}
	return int64(len(s.items))
}
func (s *PySet[T]) pySetItemsAny() any {
	if s == nil {
		return map[T]struct{}{}
	}
	return s.items
}
func (s *PySet[T]) __str__() string {
	if s == nil {
		return "set()"
	}
	return py_format_set_repr(s.items)
}

func NewPySet[T comparable]() *PySet[T] {
	return &PySet[T]{items: map[T]struct{}{}}
}

func PySetFromMap[T comparable](items any) *PySet[T] {
	if direct, ok := items.(*PySet[T]); ok {
		return direct
	}
	out := map[T]struct{}{}
	if typed, ok := items.(map[T]struct{}); ok {
		for k := range typed {
			out[k] = struct{}{}
		}
	}
	return &PySet[T]{items: out}
}

func (s *PySet[T]) clear_items() {
	if s == nil {
		return
	}
	clear(s.items)
}

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

func py_format_sequence_repr(v any) string {
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
		parts[i] = py_repr(rv.Index(i).Interface())
	}
	return "[" + strings.Join(parts, ", ") + "]"
}

func py_format_tuple_repr(v any) string {
	rv := goreflect.ValueOf(v)
	if !rv.IsValid() {
		return "()"
	}
	if rv.Kind() != goreflect.Slice && rv.Kind() != goreflect.Array {
		return gofmt.Sprint(v)
	}
	parts := make([]string, rv.Len())
	for i := 0; i < rv.Len(); i++ {
		parts[i] = py_repr(rv.Index(i).Interface())
	}
	if len(parts) == 1 {
		return "(" + parts[0] + ",)"
	}
	return "(" + strings.Join(parts, ", ") + ")"
}

func py_format_mapping_repr(v any) string {
	rv := py_unwrap_dict_value(v)
	if !rv.IsValid() || rv.Kind() != goreflect.Map {
		return "{}"
	}
	keys := rv.MapKeys()
	sort.Slice(keys, func(i, j int) bool {
		return py_str(keys[i].Interface()) < py_str(keys[j].Interface())
	})
	parts := make([]string, 0, len(keys))
	for _, key := range keys {
		value := rv.MapIndex(key)
		parts = append(parts, py_repr(key.Interface())+": "+py_repr(value.Interface()))
	}
	return "{" + strings.Join(parts, ", ") + "}"
}

func py_format_set_repr(v any) string {
	rv := goreflect.ValueOf(v)
	if !rv.IsValid() || rv.Kind() != goreflect.Map {
		return "set()"
	}
	keys := rv.MapKeys()
	if len(keys) == 0 {
		return "set()"
	}
	parts := make([]string, 0, len(keys))
	for _, key := range keys {
		parts = append(parts, py_repr(key.Interface()))
	}
	sort.Strings(parts)
	return "{" + strings.Join(parts, ", ") + "}"
}

func py_repr(v any) string {
	if v == nil {
		return "None"
	}
	switch t := v.(type) {
	case string:
		return "'" + strings.ReplaceAll(t, "'", "\\'") + "'"
	case PyTuple:
		return py_format_tuple_repr([]any(t))
	case []any:
		return py_format_sequence_repr(t)
	case bool:
		return py_str(t)
	case float32, float64:
		return py_str(t)
	case int, int8, int16, int32, int64, uint, uint8, uint16, uint32, uint64:
		return py_str(t)
	}
	if s, ok := v.(interface{ __str__() string }); ok {
		return s.__str__()
	}
	rv := goreflect.ValueOf(v)
	for rv.IsValid() && (rv.Kind() == goreflect.Interface || rv.Kind() == goreflect.Pointer) {
		if rv.IsNil() {
			return "None"
		}
		if s, ok := rv.Interface().(interface{ __str__() string }); ok {
			return s.__str__()
		}
		rv = rv.Elem()
		v = rv.Interface()
	}
	if !rv.IsValid() {
		return "None"
	}
	if rv.Kind() == goreflect.Slice || rv.Kind() == goreflect.Array {
		return py_format_sequence_repr(v)
	}
	if rv.Kind() == goreflect.Map {
		if rv.Type().Elem().Kind() == goreflect.Struct {
			return py_format_set_repr(v)
		}
		return py_format_mapping_repr(v)
	}
	return py_str(v)
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
	case PyTuple:
		return py_format_tuple_repr([]any(t))
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
		return py_format_sequence_repr(v)
	}
	if rv.Kind() == goreflect.Map {
		if rv.Type().Elem().Kind() == goreflect.Struct {
			return py_format_set_repr(v)
		}
		return py_format_mapping_repr(v)
	}
	return gofmt.Sprint(v)
}
func py_to_string(v any) string { return py_str(v) }

type PyFile struct {
	file *os.File
}

func (f *PyFile) __enter__() *PyFile {
	return f
}

func (f *PyFile) __exit__(excType any, excVal any, excTb any) {
	f.close()
}

type SystemExit int64

func NewSystemExit(code int64) *PytraErrorCarrier {
	return &PytraErrorCarrier{
		TypeId: pytraTypeRangeMin(EXCEPTION_TID),
		TypeMin: pytraTypeRangeMin(EXCEPTION_TID),
		TypeMax: pytraTypeRangeMax(EXCEPTION_TID),
		Name: "SystemExit",
		Msg:  "SystemExit(" + py_str(code) + ")",
		Value: code,
	}
}

type PytraErrorCarrier struct {
	TypeId  int64
	TypeMin int64
	TypeMax int64
	Name    string
	Msg     string
	Cause   *PytraErrorCarrier
	Value   any
}

func (e *PytraErrorCarrier) Error() string {
	if e == nil {
		return ""
	}
	return e.Msg
}

func (e *PytraErrorCarrier) __str__() string {
	if e == nil {
		return ""
	}
	return e.Msg
}

func pytraTypeRangeMin(tid int64) int64 {
	return id_table.items[int(tid*2)]
}

func pytraTypeRangeMax(tid int64) int64 {
	return id_table.items[int(tid*2+1)]
}

func pytraNewBaseException(msg string) *PytraErrorCarrier {
	return &PytraErrorCarrier{TypeId: pytraTypeRangeMin(BASE_EXCEPTION_TID), TypeMin: pytraTypeRangeMin(BASE_EXCEPTION_TID), TypeMax: pytraTypeRangeMax(BASE_EXCEPTION_TID), Name: "BaseException", Msg: msg}
}

func pytraNewException(msg string) *PytraErrorCarrier {
	return &PytraErrorCarrier{TypeId: pytraTypeRangeMin(EXCEPTION_TID), TypeMin: pytraTypeRangeMin(EXCEPTION_TID), TypeMax: pytraTypeRangeMax(EXCEPTION_TID), Name: "Exception", Msg: msg}
}

func pytraNewRuntimeError(msg string) *PytraErrorCarrier {
	return &PytraErrorCarrier{TypeId: pytraTypeRangeMin(RUNTIME_ERROR_TID), TypeMin: pytraTypeRangeMin(RUNTIME_ERROR_TID), TypeMax: pytraTypeRangeMax(RUNTIME_ERROR_TID), Name: "RuntimeError", Msg: msg}
}

func pytraNewValueError(msg string) *PytraErrorCarrier {
	return &PytraErrorCarrier{TypeId: pytraTypeRangeMin(VALUE_ERROR_TID), TypeMin: pytraTypeRangeMin(VALUE_ERROR_TID), TypeMax: pytraTypeRangeMax(VALUE_ERROR_TID), Name: "ValueError", Msg: msg}
}

func pytraNewTypeError(msg string) *PytraErrorCarrier {
	return &PytraErrorCarrier{TypeId: pytraTypeRangeMin(TYPE_ERROR_TID), TypeMin: pytraTypeRangeMin(TYPE_ERROR_TID), TypeMax: pytraTypeRangeMax(TYPE_ERROR_TID), Name: "TypeError", Msg: msg}
}

func pytraNewIndexError(msg string) *PytraErrorCarrier {
	return &PytraErrorCarrier{TypeId: pytraTypeRangeMin(INDEX_ERROR_TID), TypeMin: pytraTypeRangeMin(INDEX_ERROR_TID), TypeMax: pytraTypeRangeMax(INDEX_ERROR_TID), Name: "IndexError", Msg: msg}
}

func pytraNewKeyError(msg string) *PytraErrorCarrier {
	return &PytraErrorCarrier{TypeId: pytraTypeRangeMin(KEY_ERROR_TID), TypeMin: pytraTypeRangeMin(KEY_ERROR_TID), TypeMax: pytraTypeRangeMax(KEY_ERROR_TID), Name: "KeyError", Msg: msg}
}

func pytraEnsureRecoveredError(value any) *PytraErrorCarrier {
	switch t := value.(type) {
	case *PytraErrorCarrier:
		return t
	case interface{ pytraErrorBase() *PytraErrorCarrier }:
		return t.pytraErrorBase()
	case error:
		if strings.Contains(t.Error(), "index out of range") || strings.Contains(t.Error(), "slice bounds out of range") {
			return pytraNewIndexError(t.Error())
		}
		return pytraNewRuntimeError(t.Error())
	case string:
		if strings.Contains(t, "index out of range") || strings.Contains(t, "slice bounds out of range") {
			return pytraNewIndexError(t)
		}
		return pytraNewRuntimeError(t)
	default:
		return pytraNewRuntimeError(py_str(t))
	}
}

func pytraErrorIsInstance(err *PytraErrorCarrier, tidMin int64, tidMax int64) bool {
	if err == nil {
		return false
	}
	return err.TypeId >= tidMin && err.TypeId <= tidMax
}

func pytraAttachCause(err *PytraErrorCarrier, cause any) *PytraErrorCarrier {
	if err == nil {
		return nil
	}
	err.Cause = pytraEnsureRecoveredError(cause)
	return err
}

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

func py_TextIOWrapper_read(f *PyFile) string {
	return f.read()
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

func py_TextIOWrapper_write(f *PyFile, data any) int64 {
	return f.write(data)
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

func py_clear(v any) {
	switch t := v.(type) {
	case interface{ clear_items() }:
		t.clear_items()
		return
	}
}

func py_pop[K comparable, V any](d *PyDict[K, V], key K, defaultValue ...V) V {
	var zero V
	if d == nil {
		if len(defaultValue) > 0 {
			return defaultValue[0]
		}
		return zero
	}
	if value, ok := d.items[key]; ok {
		delete(d.items, key)
		return value
	}
	if len(defaultValue) > 0 {
		return defaultValue[0]
	}
	return zero
}

func py_setdefault[K comparable, V any](d *PyDict[K, V], key K, defaultValue V) V {
	if d == nil {
		return defaultValue
	}
	if value, ok := d.items[key]; ok {
		return value
	}
	d.items[key] = defaultValue
	return defaultValue
}

func py_call_void(fn any) {
	switch f := fn.(type) {
	case func():
		f()
	case func() *PytraErrorCarrier:
		if err := f(); err != nil {
			panic(err)
		}
	default:
		panic("py_call_void: unsupported callable")
	}
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

func py_sum[T pyNumber](values *PyList[T]) T {
	var acc T
	for _, value := range values.items {
		acc += value
	}
	return acc
}

func py_zip[A any, B any](lhs *PyList[A], rhs *PyList[B]) *PyList[[]any] {
	n := len(lhs.items)
	if len(rhs.items) < n {
		n = len(rhs.items)
	}
	out := NewPyList[[]any]()
	for i := 0; i < n; i++ {
		out.items = append(out.items, []any{lhs.items[i], rhs.items[i]})
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
	if view, ok := a.(pyListView); ok {
		items := make([]any, view.pyListLen())
		for i := 0; i < view.pyListLen(); i++ {
			items[i] = view.pyListItemAny(i)
		}
		a = items
	}
	if view, ok := b.(pyListView); ok {
		items := make([]any, view.pyListLen())
		for i := 0; i < view.pyListLen(); i++ {
			items[i] = view.pyListItemAny(i)
		}
		b = items
	}
	if view, ok := a.(pyDictAccessor); ok {
		a = view.pyDictItemsAny()
	}
	if view, ok := b.(pyDictAccessor); ok {
		b = view.pyDictItemsAny()
	}
	if goreflect.DeepEqual(a, b) {
		return true
	}
	av := goreflect.ValueOf(a)
	bv := goreflect.ValueOf(b)
	if av.IsValid() && bv.IsValid() {
		if (av.Kind() == goreflect.Slice || av.Kind() == goreflect.Array) && (bv.Kind() == goreflect.Slice || bv.Kind() == goreflect.Array) {
			if av.Len() != bv.Len() {
				return false
			}
			for i := 0; i < av.Len(); i++ {
				if !py_eq(av.Index(i).Interface(), bv.Index(i).Interface()) {
					return false
				}
			}
			return true
		}
		if av.Kind() == goreflect.Map && bv.Kind() == goreflect.Map {
			if av.Len() != bv.Len() {
				return false
			}
			iter := av.MapRange()
			for iter.Next() {
				key := iter.Key()
				var other goreflect.Value
				if key.Type().AssignableTo(bv.Type().Key()) {
					other = bv.MapIndex(key)
				} else if key.Type().ConvertibleTo(bv.Type().Key()) {
					other = bv.MapIndex(key.Convert(bv.Type().Key()))
				}
				if !other.IsValid() || !py_eq(iter.Value().Interface(), other.Interface()) {
					return false
				}
			}
			return true
		}
	}
	_, a_is_string := a.(string)
	_, b_is_string := b.(string)
	if a_is_string != b_is_string {
		return false
	}
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

func py_less_any(a any, b any) bool {
	av := goreflect.ValueOf(a)
	bv := goreflect.ValueOf(b)
	if av.IsValid() && bv.IsValid() && av.Type().ConvertibleTo(bv.Type()) {
		a = av.Convert(bv.Type()).Interface()
	}
	switch x := a.(type) {
	case int:
		return x < b.(int)
	case int8:
		return x < b.(int8)
	case int16:
		return x < b.(int16)
	case int32:
		return x < b.(int32)
	case int64:
		return x < b.(int64)
	case uint8:
		return x < b.(uint8)
	case uint16:
		return x < b.(uint16)
	case uint32:
		return x < b.(uint32)
	case uint64:
		return x < b.(uint64)
	case float32:
		return x < b.(float32)
	case float64:
		return x < b.(float64)
	case string:
		return x < b.(string)
	default:
		return py_str(a) < py_str(b)
	}
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
	case pyListView:
		for i := 0; i < h.pyListLen(); i++ {
			if py_eq(h.pyListItemAny(i), needle) {
				return true
			}
		}
		return false
	case pyDictAccessor:
		rv := py_unwrap_dict_value(h)
		if rv.IsValid() && rv.Kind() == goreflect.Map {
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
	if _, ok := v.(pyListView); ok {
		return true
	}
	rv := goreflect.ValueOf(v)
	if !rv.IsValid() {
		return false
	}
	return rv.Kind() == goreflect.Slice || rv.Kind() == goreflect.Array
}

func py_is_dict(v any) bool {
	if _, ok := v.(pyDictView); ok {
		return true
	}
	rv := goreflect.ValueOf(v)
	return rv.IsValid() && rv.Kind() == goreflect.Map
}

func py_is_set(v any) bool {
	rv := goreflect.ValueOf(v)
	if !rv.IsValid() || rv.Kind() != goreflect.Map {
		return false
	}
	return rv.Type().Elem().Kind() == goreflect.Struct
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

func py_range(args ...int64) *PyList[int64] {
	var start int64 = 0
	var stop int64 = 0
	var step int64 = 1
	switch len(args) {
	case 1:
		stop = args[0]
	case 2:
		start = args[0]
		stop = args[1]
	case 3:
		start = args[0]
		stop = args[1]
		step = args[2]
	default:
		panic("py_range: expected 1..3 arguments")
	}
	if step == 0 {
		panic("py_range: step must not be zero")
	}
	out := NewPyList[int64]()
	if step > 0 {
		for cur := start; cur < stop; cur += step {
			out.items = append(out.items, cur)
		}
		return out
	}
	for cur := start; cur > stop; cur += step {
		out.items = append(out.items, cur)
	}
	return out
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

func py_index(items any, needle any) int64 {
	switch seq := items.(type) {
	case pyListView:
		for i := 0; i < seq.pyListLen(); i++ {
			if py_eq(seq.pyListItemAny(i), needle) {
				return int64(i)
			}
		}
		panic("value is not in list")
	}
	rv := goreflect.ValueOf(items)
	if rv.IsValid() && (rv.Kind() == goreflect.Slice || rv.Kind() == goreflect.Array) {
		for i := 0; i < rv.Len(); i++ {
			if py_eq(rv.Index(i).Interface(), needle) {
				return int64(i)
			}
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
func py_str_join(sep string, items any) string {
	switch seq := items.(type) {
	case []string:
		return strings.Join(seq, sep)
	case *PyList[string]:
		return strings.Join(seq.items, sep)
	case []any:
		parts := make([]string, 0, len(seq))
		for _, item := range seq {
			parts = append(parts, py_str(item))
		}
		return strings.Join(parts, sep)
	case *PyList[any]:
		parts := make([]string, 0, len(seq.items))
		for _, item := range seq.items {
			parts = append(parts, py_str(item))
		}
		return strings.Join(parts, sep)
	default:
		return strings.Join([]string{py_str(items)}, sep)
	}
}
func py_str_replace(s, old, new_ string) string     { return strings.ReplaceAll(s, old, new_) }
func py_str_split(s, sep string) []string           { return strings.Split(s, sep) }
func py_str_startswith(s, prefix string) bool       { return strings.HasPrefix(s, prefix) }
func py_str_endswith(s, suffix string) bool         { return strings.HasSuffix(s, suffix) }
func py_str_upper(s string) string                  { return strings.ToUpper(s) }
func py_str_lower(s string) string                  { return strings.ToLower(s) }
func py_str_find(s, sub string) int64               { return int64(strings.Index(s, sub)) }
func py_str_count(s, sub string) int64              { return int64(strings.Count(s, sub)) }
func py_str_rfind(s, sub string) int64              { return int64(strings.LastIndex(s, sub)) }
func py_str_index(s, sub string) int64 {
	idx := strings.Index(s, sub)
	if idx < 0 {
		panic(pytraNewValueError("substring not found"))
	}
	return int64(idx)
}
func py_list_index(seq any, needle any) int64 {
	rv := goreflect.ValueOf(seq)
	if rv.IsValid() && rv.Kind() == goreflect.Pointer && !rv.IsNil() {
		elem := rv.Elem()
		if elem.IsValid() && elem.Kind() == goreflect.Struct {
			itemsField := elem.FieldByName("items")
			if itemsField.IsValid() && (itemsField.Kind() == goreflect.Slice || itemsField.Kind() == goreflect.Array) {
				rv = itemsField
			}
		}
	}
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

func py_enumerate(seq any, start ...int64) *PyList[[]any] {
	idx := int64(0)
	if len(start) > 0 {
		idx = start[0]
	}
	out := NewPyList[[]any]()
	if listView, ok := seq.(pyListView); ok {
		out.items = make([][]any, 0, listView.pyListLen())
		for i := 0; i < listView.pyListLen(); i++ {
			out.items = append(out.items, []any{idx, listView.pyListItemAny(i)})
			idx += 1
		}
		return out
	}
	rv := goreflect.ValueOf(seq)
	if rv.IsValid() && rv.Kind() == goreflect.Pointer && !rv.IsNil() {
		elem := rv.Elem()
		if elem.IsValid() && elem.Kind() == goreflect.Struct {
			itemsField := elem.FieldByName("items")
			if itemsField.IsValid() && (itemsField.Kind() == goreflect.Slice || itemsField.Kind() == goreflect.Array) {
				rv = itemsField
			}
		}
	}
	if !rv.IsValid() || (rv.Kind() != goreflect.Slice && rv.Kind() != goreflect.Array) {
		return out
	}
	out.items = make([][]any, 0, rv.Len())
	for i := 0; i < rv.Len(); i++ {
		out.items = append(out.items, []any{idx, rv.Index(i).Interface()})
		idx += 1
	}
	return out
}

func py_reversed[T any](seq *PyList[T]) *PyList[T] {
	src := seq.items
	out := make([]T, len(src))
	for i := range src {
		out[len(src)-1-i] = src[i]
	}
	return &PyList[T]{items: out}
}

func py_reversed_object[T any](seq *PyList[T]) *PyList[T] {
	return py_reversed(seq)
}

func py_sorted[T any](seq *PyList[T]) *PyList[T] {
	out := make([]T, len(seq.items))
	copy(out, seq.items)
	sort.Slice(out, func(i int, j int) bool {
		return py_less_any(out[i], out[j])
	})
	return &PyList[T]{items: out}
}

func py_reverse(v any) {
	if t, ok := v.(interface{ reverse_items() }); ok {
		t.reverse_items()
		return
	}
}

func py_sort(v any) {
	if t, ok := v.(interface{ sort_items() }); ok {
		t.sort_items()
	}
}

func py_discard[K comparable](s any, key K) {
	switch t := s.(type) {
	case map[K]struct{}:
		delete(t, key)
	case *PySet[K]:
		if t != nil {
			delete(t.items, key)
		}
	}
}

func py_remove[K comparable](s any, key K) {
	switch t := s.(type) {
	case map[K]struct{}:
		if _, ok := t[key]; !ok {
			panic("KeyError")
		}
		delete(t, key)
	case *PySet[K]:
		if t == nil {
			panic("KeyError")
		}
		if _, ok := t.items[key]; !ok {
			panic("KeyError")
		}
		delete(t.items, key)
	default:
		panic("KeyError")
	}
}

func py_unwrap_dict_value(m any) goreflect.Value {
	if accessor, ok := m.(pyDictAccessor); ok {
		mv := goreflect.ValueOf(accessor.pyDictItemsAny())
		if mv.IsValid() && mv.Kind() == goreflect.Map {
			return mv
		}
	}
	mv := goreflect.ValueOf(m)
	if !mv.IsValid() {
		return goreflect.Value{}
	}
	if mv.Kind() == goreflect.Map {
		return mv
	}
	return goreflect.Value{}
}

// Dict
func py_dict_get(m any, key any, def_ any) any {
	mv := py_unwrap_dict_value(m)
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
	mv := py_unwrap_dict_value(m)
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
	mv := py_unwrap_dict_value(m)
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
	mv := py_unwrap_dict_value(m)
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
	if list, ok := v.(pyListView); ok {
		out := make([]any, list.pyListLen())
		for i := 0; i < list.pyListLen(); i++ {
			out[i] = list.pyListItemAny(i)
		}
		return out
	}
	if dict, ok := v.(pyDictAccessor); ok {
		v = dict.pyDictItemsAny()
	} else if set, ok := v.(pySetAccessor); ok {
		v = set.pySetItemsAny()
	}
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
	if rv.Kind() == goreflect.Struct {
		itemsField := rv.FieldByName("items")
		if itemsField.IsValid() && itemsField.CanInterface() {
			rv = itemsField
		}
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

func py_set_update(dst any, values any) any {
	if accessor, ok := dst.(pySetAccessor); ok {
		dst = accessor.pySetItemsAny()
	}
	target := goreflect.ValueOf(dst)
	if !target.IsValid() {
		return dst
	}
	if target.Kind() == goreflect.Ptr && !target.IsNil() {
		elem := target.Elem()
		if elem.Kind() == goreflect.Struct {
			items := elem.FieldByName("items")
			if items.IsValid() {
				target = items
			}
		}
	}
	if target.Kind() != goreflect.Map {
		return dst
	}
	if target.IsNil() {
		target.Set(goreflect.MakeMap(target.Type()))
	}
	keyType := target.Type().Key()
	appendValue := func(raw goreflect.Value) {
		if !raw.IsValid() {
			return
		}
		if raw.Type().AssignableTo(keyType) {
			target.SetMapIndex(raw, goreflect.Zero(target.Type().Elem()))
			return
		}
		if raw.Type().ConvertibleTo(keyType) {
			target.SetMapIndex(raw.Convert(keyType), goreflect.Zero(target.Type().Elem()))
		}
	}
	var visit func(v goreflect.Value)
	visit = func(v goreflect.Value) {
		if !v.IsValid() {
			return
		}
		if v.CanInterface() {
			if accessor, ok := v.Interface().(pySetAccessor); ok {
				visit(goreflect.ValueOf(accessor.pySetItemsAny()))
				return
			}
		}
		if v.Kind() == goreflect.Interface || v.Kind() == goreflect.Ptr {
			if v.IsNil() {
				return
			}
			visit(v.Elem())
			return
		}
		switch v.Kind() {
		case goreflect.Slice, goreflect.Array:
			for i := 0; i < v.Len(); i++ {
				appendValue(v.Index(i))
			}
		case goreflect.Map:
			iter := v.MapRange()
			for iter.Next() {
				appendValue(iter.Key())
			}
		}
	}
	visit(goreflect.ValueOf(values))
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
	// Handle *PyDict[string, V] via its pyMapStringAny() method.
	type pyMapStringAnyer interface {
		pyMapStringAny() map[string]any
	}
	if d, ok := v.(pyMapStringAnyer); ok {
		return d.pyMapStringAny()
	}
	// Handle plain map[string]V via reflection
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
	case bool:
		if t {
			return 1.0
		}
		return 0.0
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
