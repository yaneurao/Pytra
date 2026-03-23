// Go ネイティブ変換向け Python 互換ランタイム補助。
package main

import (
	"encoding/json"
	"fmt"
	"math"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"time"
	"unicode"
)

// ---------- PyList: reference-semantic list wrapper ----------

type PyList struct {
	Items []any
}

func NewPyList(items ...any) *PyList {
	return &PyList{Items: items}
}

func (pl *PyList) Append(v any) {
	pl.Items = append(pl.Items, v)
}

func (pl *PyList) AppendSlice(src []any) {
	pl.Items = append(pl.Items, src...)
}

func (pl *PyList) Len() int64 {
	return int64(len(pl.Items))
}

func (pl *PyList) Get(i int64) any {
	if i < 0 {
		i += int64(len(pl.Items))
	}
	return pl.Items[i]
}

func (pl *PyList) Set(i int64, v any) {
	if i < 0 {
		i += int64(len(pl.Items))
	}
	pl.Items[i] = v
}

func (pl *PyList) Pop(idx any) any {
	n := len(pl.Items)
	i := n - 1
	if idx != nil {
		i = int(__pytra_int_raw(idx))
		if i < 0 {
			i += n
		}
	}
	val := pl.Items[i]
	pl.Items = append(pl.Items[:i], pl.Items[i+1:]...)
	return val
}

// __pytra_int_raw is a minimal int coercion that avoids circular dependency
// with the full __pytra_int (which may reference PyList).
func __pytra_int_raw(v any) int64 {
	switch t := v.(type) {
	case int:
		return int64(t)
	case int64:
		return t
	case int32:
		return int64(t)
	case uint8:
		return int64(t)
	case float64:
		return int64(t)
	case nil:
		return 0
	default:
		return 0
	}
}

func __pytra_as_PyList(v any) *PyList {
	if t, ok := v.(*PyList); ok {
		return t
	}
	if t, ok := v.([]any); ok {
		return &PyList{Items: t}
	}
	return NewPyList()
}

func pyToString(v any) string {
	switch x := v.(type) {
	case nil:
		return "None"
	case bool:
		if x {
			return "True"
		}
		return "False"
	case string:
		return x
	case int:
		return strconv.Itoa(x)
	case int64:
		return strconv.FormatInt(x, 10)
	case float64:
		return strconv.FormatFloat(x, 'f', -1, 64)
	case []any:
		parts := make([]string, 0, len(x))
		for _, it := range x {
			parts = append(parts, pyToString(it))
		}
		return "[" + strings.Join(parts, ", ") + "]"
	case *PyList:
		parts := make([]string, 0, len(x.Items))
		for _, it := range x.Items {
			parts = append(parts, pyToString(it))
		}
		return "[" + strings.Join(parts, ", ") + "]"
	case map[any]any:
		parts := make([]string, 0, len(x))
		for k, v := range x {
			parts = append(parts, pyToString(k)+": "+pyToString(v))
		}
		return "{" + strings.Join(parts, ", ") + "}"
	case Path:
		return x.value
	case *Path:
		if x == nil {
			return ""
		}
		return x.value
	case pyPath:
		return x.value
	default:
		return fmt.Sprint(x)
	}
}

func pyPrint(args ...any) {
	parts := make([]string, 0, len(args))
	for _, a := range args {
		parts = append(parts, pyToString(a))
	}
	fmt.Println(strings.Join(parts, " "))
}

func pyBool(v any) bool {
	switch x := v.(type) {
	case nil:
		return false
	case bool:
		return x
	case int:
		return x != 0
	case int64:
		return x != 0
	case float64:
		return x != 0.0
	case string:
		return x != ""
	case []any:
		return len(x) > 0
	case *PyList:
		return len(x.Items) > 0
	case []byte:
		return len(x) > 0
	case map[any]any:
		return len(x) > 0
	default:
		return true
	}
}

func pyLen(v any) int {
	switch x := v.(type) {
	case string:
		return len([]rune(x))
	case []any:
		return len(x)
	case *PyList:
		return len(x.Items)
	case []byte:
		return len(x)
	case map[any]any:
		return len(x)
	default:
		panic("len() unsupported type")
	}
}

func pyRange(start, stop, step int) []any {
	if step == 0 {
		panic("range() step must not be zero")
	}
	out := []any{}
	if step > 0 {
		for i := start; i < stop; i += step {
			out = append(out, i)
		}
	} else {
		for i := start; i > stop; i += step {
			out = append(out, i)
		}
	}
	return out
}

func pyToFloat(v any) float64 {
	switch x := v.(type) {
	case int:
		return float64(x)
	case int64:
		return float64(x)
	case float64:
		return x
	case bool:
		if x {
			return 1.0
		}
		return 0.0
	default:
		panic("cannot convert to float")
	}
}

func pyToInt(v any) int {
	switch x := v.(type) {
	case int:
		return x
	case int64:
		return int(x)
	case float64:
		return int(math.Trunc(x))
	case bool:
		if x {
			return 1
		}
		return 0
	default:
		panic("cannot convert to int")
	}
}

func pyAdd(a, b any) any {
	if sa, ok := a.(string); ok {
		return sa + pyToString(b)
	}
	if sb, ok := b.(string); ok {
		return pyToString(a) + sb
	}
	_, aInt := a.(int)
	_, bInt := b.(int)
	if aInt && bInt {
		return pyToInt(a) + pyToInt(b)
	}
	return pyToFloat(a) + pyToFloat(b)
}
func pySub(a, b any) any {
	_, aInt := a.(int)
	_, bInt := b.(int)
	if aInt && bInt {
		return pyToInt(a) - pyToInt(b)
	}
	return pyToFloat(a) - pyToFloat(b)
}
func pyMul(a, b any) any {
	_, aInt := a.(int)
	_, bInt := b.(int)
	if aInt && bInt {
		return pyToInt(a) * pyToInt(b)
	}
	return pyToFloat(a) * pyToFloat(b)
}
func pyDiv(a, b any) any      { return pyToFloat(a) / pyToFloat(b) }
func pyFloorDiv(a, b any) any { return int(math.Floor(pyToFloat(a) / pyToFloat(b))) }
func pyMod(a, b any) any {
	ai := pyToInt(a)
	bi := pyToInt(b)
	r := ai % bi
	if r != 0 && ((r > 0) != (bi > 0)) {
		r += bi
	}
	return r
}
func pyMin(values ...any) any {
	if len(values) == 0 {
		panic("min() arg is empty")
	}
	out := values[0]
	for i := 1; i < len(values); i++ {
		a := out
		b := values[i]
		if _, ok := a.(int); ok {
			if _, ok2 := b.(int); ok2 {
				ai := pyToInt(a)
				bi := pyToInt(b)
				if bi < ai {
					out = bi
				}
				continue
			}
		}
		af := pyToFloat(a)
		bf := pyToFloat(b)
		if bf < af {
			out = bf
		}
	}
	return out
}
func pyMax(values ...any) any {
	if len(values) == 0 {
		panic("max() arg is empty")
	}
	out := values[0]
	for i := 1; i < len(values); i++ {
		a := out
		b := values[i]
		if _, ok := a.(int); ok {
			if _, ok2 := b.(int); ok2 {
				ai := pyToInt(a)
				bi := pyToInt(b)
				if bi > ai {
					out = bi
				}
				continue
			}
		}
		af := pyToFloat(a)
		bf := pyToFloat(b)
		if bf > af {
			out = bf
		}
	}
	return out
}
func pyLShift(a, b any) any { return pyToInt(a) << uint(pyToInt(b)) }
func pyRShift(a, b any) any { return pyToInt(a) >> uint(pyToInt(b)) }
func pyBitAnd(a, b any) any { return pyToInt(a) & pyToInt(b) }
func pyBitOr(a, b any) any  { return pyToInt(a) | pyToInt(b) }
func pyBitXor(a, b any) any { return pyToInt(a) ^ pyToInt(b) }
func pyNeg(a any) any {
	if _, ok := a.(int); ok {
		return -pyToInt(a)
	}
	return -pyToFloat(a)
}

func pyEq(a, b any) bool { return pyToString(a) == pyToString(b) }
func pyNe(a, b any) bool { return !pyEq(a, b) }
func pyLt(a, b any) bool { return pyToFloat(a) < pyToFloat(b) }
func pyLe(a, b any) bool { return pyToFloat(a) <= pyToFloat(b) }
func pyGt(a, b any) bool { return pyToFloat(a) > pyToFloat(b) }
func pyGe(a, b any) bool { return pyToFloat(a) >= pyToFloat(b) }

func pyIn(item, container any) bool {
	switch c := container.(type) {
	case string:
		return strings.Contains(c, pyToString(item))
	case []any:
		for _, v := range c {
			if pyEq(v, item) {
				return true
			}
		}
		return false
	case *PyList:
		for _, v := range c.Items {
			if pyEq(v, item) {
				return true
			}
		}
		return false
	case map[any]any:
		_, ok := c[item]
		return ok
	default:
		return false
	}
}

func pyIter(value any) []any {
	switch v := value.(type) {
	case []any:
		return v
	case *PyList:
		return v.Items
	case []byte:
		out := make([]any, 0, len(v))
		for _, b := range v {
			out = append(out, int(b))
		}
		return out
	case string:
		out := []any{}
		for _, ch := range []rune(v) {
			out = append(out, string(ch))
		}
		return out
	case map[any]any:
		out := []any{}
		for k := range v {
			out = append(out, k)
		}
		return out
	default:
		panic("iter unsupported")
	}
}

func pyTernary(cond bool, a any, b any) any {
	if cond {
		return a
	}
	return b
}

func pyListFromIter(value any) any {
	it := pyIter(value)
	out := make([]any, len(it))
	copy(out, it)
	return out
}

func pySlice(value any, start any, end any) any {
	s := 0
	e := 0
	switch v := value.(type) {
	case string:
		r := []rune(v)
		n := len(r)
		if start == nil {
			s = 0
		} else {
			s = pyToInt(start)
			if s < 0 {
				s += n
			}
			if s < 0 {
				s = 0
			}
			if s > n {
				s = n
			}
		}
		if end == nil {
			e = n
		} else {
			e = pyToInt(end)
			if e < 0 {
				e += n
			}
			if e < 0 {
				e = 0
			}
			if e > n {
				e = n
			}
		}
		if s > e {
			s = e
		}
		return string(r[s:e])
	case []any:
		n := len(v)
		if start == nil {
			s = 0
		} else {
			s = pyToInt(start)
			if s < 0 {
				s += n
			}
			if s < 0 {
				s = 0
			}
			if s > n {
				s = n
			}
		}
		if end == nil {
			e = n
		} else {
			e = pyToInt(end)
			if e < 0 {
				e += n
			}
			if e < 0 {
				e = 0
			}
			if e > n {
				e = n
			}
		}
		if s > e {
			s = e
		}
		out := make([]any, e-s)
		copy(out, v[s:e])
		return out
	case *PyList:
		n := len(v.Items)
		if start == nil {
			s = 0
		} else {
			s = pyToInt(start)
			if s < 0 {
				s += n
			}
			if s < 0 {
				s = 0
			}
			if s > n {
				s = n
			}
		}
		if end == nil {
			e = n
		} else {
			e = pyToInt(end)
			if e < 0 {
				e += n
			}
			if e < 0 {
				e = 0
			}
			if e > n {
				e = n
			}
		}
		if s > e {
			s = e
		}
		out := make([]any, e-s)
		copy(out, v.Items[s:e])
		return &PyList{Items: out}
	default:
		panic("slice unsupported")
	}
}

func pyGet(value any, key any) any {
	switch v := value.(type) {
	case []any:
		i := pyToInt(key)
		if i < 0 {
			i += len(v)
		}
		return v[i]
	case *PyList:
		i := pyToInt(key)
		if i < 0 {
			i += len(v.Items)
		}
		return v.Items[i]
	case []byte:
		i := pyToInt(key)
		if i < 0 {
			i += len(v)
		}
		return int(v[i])
	case map[any]any:
		return v[key]
	case string:
		r := []rune(v)
		i := pyToInt(key)
		if i < 0 {
			i += len(r)
		}
		return string(r[i])
	default:
		panic("subscript unsupported")
	}
}

func pySet(value any, key any, newValue any) {
	switch v := value.(type) {
	case []any:
		i := pyToInt(key)
		if i < 0 {
			i += len(v)
		}
		v[i] = newValue
	case *PyList:
		i := pyToInt(key)
		if i < 0 {
			i += len(v.Items)
		}
		v.Items[i] = newValue
	case []byte:
		i := pyToInt(key)
		if i < 0 {
			i += len(v)
		}
		v[i] = byte(pyToInt(newValue))
	case map[any]any:
		v[key] = newValue
	default:
		panic("setitem unsupported")
	}
}

func pyPop(lst *any, idx any) any {
	switch v := (*lst).(type) {
	case *PyList:
		return v.Pop(idx)
	default:
		arr := (*lst).([]any)
		n := len(arr)
		i := n - 1
		if idx != nil {
			i = pyToInt(idx)
			if i < 0 {
				i += n
			}
		}
		val := arr[i]
		arr = append(arr[:i], arr[i+1:]...)
		*lst = arr
		return val
	}
}

func pyPopAt(container any, key any, idx any) any {
	lst := pyGet(container, key)
	switch pl := lst.(type) {
	case *PyList:
		return pl.Pop(idx)
	default:
		val := pyPop(&lst, idx)
		pySet(container, key, lst)
		return val
	}
}

func pyOrd(v any) any {
	s := pyToString(v)
	r := []rune(s)
	return int(r[0])
}

func pyChr(v any) any { return string(rune(pyToInt(v))) }

func pyBytearray(size any) any {
	if size == nil {
		return []byte{}
	}
	n := pyToInt(size)
	out := make([]byte, n)
	return out
}

func pyBytes(v any) any { return v }

func pyAppend(seq any, value any) any {
	switch s := seq.(type) {
	case []any:
		return append(s, value)
	case *PyList:
		s.Append(value)
		return s
	case []byte:
		return append(s, byte(pyToInt(value)))
	default:
		panic("append unsupported type")
	}
}

func pyIsDigit(v any) bool {
	s := pyToString(v)
	if s == "" {
		return false
	}
	for _, ch := range s {
		if ch < '0' || ch > '9' {
			return false
		}
	}
	return true
}

func pyIsAlpha(v any) bool {
	s := pyToString(v)
	if s == "" {
		return false
	}
	for _, ch := range s {
		if !((ch >= 'a' && ch <= 'z') || (ch >= 'A' && ch <= 'Z')) {
			return false
		}
	}
	return true
}

func pyTryCatch(body func() any, handler func(any) any, finalizer func()) (ret any) {
	defer finalizer()
	defer func() {
		if r := recover(); r != nil {
			ret = handler(r)
		}
	}()
	ret = body()
	return
}

// -------- time/math helper --------

func pyPerfCounter() any {
	return float64(time.Now().UnixNano()) / 1_000_000_000.0
}

func pyMathSqrt(v any) float64  { return math.Sqrt(pyToFloat(v)) }
func pyMathSin(v any) float64   { return math.Sin(pyToFloat(v)) }
func pyMathCos(v any) float64   { return math.Cos(pyToFloat(v)) }
func pyMathTan(v any) float64   { return math.Tan(pyToFloat(v)) }
func pyMathExp(v any) float64   { return math.Exp(pyToFloat(v)) }
func pyMathLog(v any) float64   { return math.Log(pyToFloat(v)) }
func pyMathLog10(v any) float64 { return math.Log10(pyToFloat(v)) }
func pyMathFabs(v any) float64  { return math.Abs(pyToFloat(v)) }
func pyMathFloor(v any) float64 { return float64(math.Floor(pyToFloat(v))) }
func pyMathCeil(v any) float64  { return float64(math.Ceil(pyToFloat(v))) }
func pyMathPow(a any, b any) float64 {
	return math.Pow(pyToFloat(a), pyToFloat(b))
}
func pyMathPi() float64 { return math.Pi }
func pyMathE() float64  { return math.E }

// -------- pathlib helper --------

type pyPath struct {
	value string
}

type Path struct {
	value  string
	parent *Path
	name   string
	stem   string
}

func __pytra_new_path(value string, shallowParent bool) *Path {
	p := &Path{value: value}
	base := filepath.Base(value)
	p.name = base
	ext := filepath.Ext(base)
	p.stem = strings.TrimSuffix(base, ext)
	parentText := filepath.Dir(value)
	if parentText == value {
		p.parent = p
	} else if shallowParent {
		p.parent = p
	} else {
		p.parent = __pytra_new_path(parentText, true)
	}
	return p
}

func NewPath(v any) *Path {
	return __pytra_new_path(pyPathString(v), false)
}

func __pytra_as_Path(v any) *Path {
	if p, ok := v.(*Path); ok {
		return p
	}
	if p, ok := v.(Path); ok {
		cp := p
		return &cp
	}
	return NewPath(v)
}

func (p *Path) String() string {
	if p == nil {
		return ""
	}
	return p.value
}

func (p *Path) exists() any {
	return pyPathExists(p)
}

func (p *Path) read_text() any {
	return pyPathReadText(p)
}

func (p *Path) write_text(args ...any) any {
	if len(args) == 0 {
		return nil
	}
	// Accept (content) or (content, encoding) — encoding is ignored (always UTF-8).
	return pyPathWriteText(p, args[0])
}

func (p *Path) mkdir(args ...any) any {
	parents := any(false)
	existOK := any(false)
	if len(args) >= 1 {
		parents = args[0]
	}
	if len(args) >= 2 {
		existOK = args[1]
	}
	return pyPathMkdir(p, parents, existOK)
}

func (p *Path) resolve() any {
	return pyPathResolve(p)
}

func pyPathString(v any) string {
	if p, ok := v.(pyPath); ok {
		return p.value
	}
	if p, ok := v.(Path); ok {
		return p.value
	}
	if p, ok := v.(*Path); ok {
		if p == nil {
			return ""
		}
		return p.value
	}
	return pyToString(v)
}

func pyPathNew(v any) any {
	return pyPath{value: pyPathString(v)}
}

func pyPathJoin(base any, child any) any {
	return pyPath{value: filepath.Join(pyPathString(base), pyPathString(child))}
}

func pyPathResolve(v any) any {
	p, err := filepath.Abs(pyPathString(v))
	if err != nil {
		panic(err)
	}
	return pyPath{value: p}
}

func pyPathParent(v any) any {
	return pyPath{value: filepath.Dir(pyPathString(v))}
}

func pyPathName(v any) any {
	return filepath.Base(pyPathString(v))
}

func pyPathStem(v any) any {
	base := filepath.Base(pyPathString(v))
	ext := filepath.Ext(base)
	return strings.TrimSuffix(base, ext)
}

func pyPathExists(v any) any {
	_, err := os.Stat(pyPathString(v))
	return err == nil
}

func pyPathReadText(v any) any {
	b, err := os.ReadFile(pyPathString(v))
	if err != nil {
		panic(err)
	}
	return string(b)
}

func pyPathWriteText(v any, content any) any {
	if err := os.WriteFile(pyPathString(v), []byte(pyToString(content)), 0o644); err != nil {
		panic(err)
	}
	return nil
}

func pyPathMkdir(v any, parents any, existOK any) any {
	p := pyPathString(v)
	if pyBool(parents) {
		if err := os.MkdirAll(p, 0o755); err != nil {
			panic(err)
		}
		return nil
	}
	err := os.Mkdir(p, 0o755)
	if err != nil {
		if pyBool(existOK) && os.IsExist(err) {
			return nil
		}
		panic(err)
	}
	return nil
}

func __pytra_any_to_bytes(v any) []byte {
	switch t := v.(type) {
	case []byte:
		out := make([]byte, len(t))
		copy(out, t)
		return out
	case []any:
		out := make([]byte, 0, len(t))
		i := 0
		for i < len(t) {
			out = append(out, byte(__pytra_int(t[i])))
			i += 1
		}
		return out
	case *PyList:
		out := make([]byte, 0, len(t.Items))
		i := 0
		for i < len(t.Items) {
			out = append(out, byte(__pytra_int(t.Items[i])))
			i += 1
		}
		return out
	case string:
		return []byte(t)
	default:
		return []byte(pyToString(v))
	}
}

type PyFile struct {
	path string
	mode string
}

func open(path any, mode string) PyFile {
	return PyFile{path: pyPathString(path), mode: mode}
}

func (f PyFile) write(data any) {
	bytes := __pytra_any_to_bytes(data)
	dir := filepath.Dir(f.path)
	if dir != "" && dir != "." {
		_ = os.MkdirAll(dir, 0o755)
	}
	if f.mode == "ab" || f.mode == "a" {
		existing, err := os.ReadFile(f.path)
		if err == nil {
			bytes = append(existing, bytes...)
		}
	}
	if err := os.WriteFile(f.path, bytes, 0o644); err != nil {
		panic(err)
	}
}

func (f PyFile) close() {}

// -------- json helper --------

func pyToJSONValue(v any) any {
	switch x := v.(type) {
	case nil:
		return nil
	case bool:
		return x
	case int:
		return int64(x)
	case int64:
		return x
	case float64:
		return x
	case string:
		return x
	case Path:
		return x.value
	case *Path:
		if x == nil {
			return ""
		}
		return x.value
	case pyPath:
		return x.value
	case []byte:
		out := make([]any, 0, len(x))
		for _, b := range x {
			out = append(out, int64(b))
		}
		return out
	case []any:
		out := make([]any, 0, len(x))
		for _, it := range x {
			out = append(out, pyToJSONValue(it))
		}
		return out
	case *PyList:
		out := make([]any, 0, len(x.Items))
		for _, it := range x.Items {
			out = append(out, pyToJSONValue(it))
		}
		return out
	case map[any]any:
		out := map[string]any{}
		for k, v := range x {
			out[pyToString(k)] = pyToJSONValue(v)
		}
		return out
	default:
		return pyToString(v)
	}
}

func pyFromJSONValue(v any) any {
	switch x := v.(type) {
	case nil:
		return nil
	case bool:
		return x
	case string:
		return x
	case json.Number:
		if i, err := x.Int64(); err == nil {
			return int64(i)
		}
		if f, err := x.Float64(); err == nil {
			return f
		}
		return x.String()
	case float64:
		return x
	case []any:
		out := make([]any, 0, len(x))
		for _, it := range x {
			out = append(out, pyFromJSONValue(it))
		}
		return out
	case *PyList:
		out := make([]any, 0, len(x.Items))
		for _, it := range x.Items {
			out = append(out, pyFromJSONValue(it))
		}
		return out
	case map[string]any:
		out := map[any]any{}
		for k, v := range x {
			out[k] = pyFromJSONValue(v)
		}
		return out
	default:
		return x
	}
}

func pyJsonDumps(v any) any {
	b, err := json.Marshal(pyToJSONValue(v))
	if err != nil {
		panic(err)
	}
	return string(b)
}

func pyJsonLoads(v any) any {
	dec := json.NewDecoder(strings.NewReader(pyToString(v)))
	dec.UseNumber()
	var out any
	if err := dec.Decode(&out); err != nil {
		panic(err)
	}
	return pyFromJSONValue(out)
}

// ---- legacy go emitter helper compatibility ----
func __pytra_noop(args ...any) {}

func __pytra_assert(args ...any) string {
	_ = args
	return "True"
}

func __pytra_perf_counter() float64 {
	return float64(time.Now().UnixNano()) / 1_000_000_000.0
}

func __pytra_truthy(v any) bool {
	switch t := v.(type) {
	case nil:
		return false
	case bool:
		return t
	case int:
		return t != 0
	case int64:
		return t != 0
	case float64:
		return t != 0.0
	case string:
		return t != ""
	case []any:
		return len(t) != 0
	case *PyList:
		return len(t.Items) != 0
	case map[any]any:
		return len(t) != 0
	default:
		return true
	}
}

func __pytra_int(v any) int64 {
	switch t := v.(type) {
	case nil:
		return 0
	case int:
		return int64(t)
	case int64:
		return t
	case int32:
		return int64(t)
	case uint8:
		return int64(t)
	case float64:
		return int64(t)
	case bool:
		if t {
			return 1
		}
		return 0
	case string:
		if t == "" {
			return 0
		}
		n, err := strconv.ParseInt(t, 10, 64)
		if err != nil {
			return 0
		}
		return n
	default:
		return 0
	}
}

func __pytra_float(v any) float64 {
	switch t := v.(type) {
	case nil:
		return 0.0
	case int:
		return float64(t)
	case int64:
		return float64(t)
	case float64:
		return t
	case bool:
		if t {
			return 1.0
		}
		return 0.0
	case string:
		if t == "" {
			return 0.0
		}
		n, err := strconv.ParseFloat(t, 64)
		if err != nil {
			return 0.0
		}
		return n
	default:
		return 0.0
	}
}

// py_to_string is the bare-name alias used by transpiled code (e.g. assertions).
func py_to_string(v any) string { return pyToString(v) }

// __pytra_as_Any is identity — Go's any already holds all types.
func __pytra_as_Any(v any) any { return v }

func __pytra_str(v any) string {
	if v == nil {
		return ""
	}
	switch t := v.(type) {
	case string:
		return t
	default:
		return fmt.Sprint(v)
	}
}

func __pytra_len(v any) int64 {
	switch t := v.(type) {
	case nil:
		return 0
	case string:
		return int64(len([]rune(t)))
	case []any:
		return int64(len(t))
	case *PyList:
		return int64(len(t.Items))
	case map[any]any:
		return int64(len(t))
	default:
		return 0
	}
}

func __pytra_index(i int64, n int64) int64 {
	if i < 0 {
		i += n
	}
	return i
}

func __pytra_get_index(container any, index any) any {
	switch t := container.(type) {
	case []any:
		if len(t) == 0 {
			return nil
		}
		i := __pytra_index(__pytra_int(index), int64(len(t)))
		if i < 0 || i >= int64(len(t)) {
			return nil
		}
		return t[i]
	case *PyList:
		if len(t.Items) == 0 {
			return nil
		}
		i := __pytra_index(__pytra_int(index), int64(len(t.Items)))
		if i < 0 || i >= int64(len(t.Items)) {
			return nil
		}
		return t.Items[i]
	case map[any]any:
		return t[index]
	case string:
		runes := []rune(t)
		if len(runes) == 0 {
			return ""
		}
		i := __pytra_index(__pytra_int(index), int64(len(runes)))
		if i < 0 || i >= int64(len(runes)) {
			return ""
		}
		return string(runes[i])
	default:
		return nil
	}
}

func __pytra_set_index(container any, index any, value any) {
	switch t := container.(type) {
	case []any:
		if len(t) == 0 {
			return
		}
		i := __pytra_index(__pytra_int(index), int64(len(t)))
		if i < 0 || i >= int64(len(t)) {
			return
		}
		t[i] = value
	case *PyList:
		if len(t.Items) == 0 {
			return
		}
		i := __pytra_index(__pytra_int(index), int64(len(t.Items)))
		if i < 0 || i >= int64(len(t.Items)) {
			return
		}
		t.Items[i] = value
	case map[any]any:
		t[index] = value
	}
}

func __pytra_slice(container any, lower any, upper any) any {
	switch t := container.(type) {
	case string:
		runes := []rune(t)
		n := int64(len(runes))
		lo := __pytra_index(__pytra_int(lower), n)
		hi := __pytra_index(__pytra_int(upper), n)
		if lo < 0 {
			lo = 0
		}
		if hi < 0 {
			hi = 0
		}
		if lo > n {
			lo = n
		}
		if hi > n {
			hi = n
		}
		if hi < lo {
			hi = lo
		}
		return string(runes[lo:hi])
	case []any:
		n := int64(len(t))
		lo := __pytra_index(__pytra_int(lower), n)
		hi := __pytra_index(__pytra_int(upper), n)
		if lo < 0 {
			lo = 0
		}
		if hi < 0 {
			hi = 0
		}
		if lo > n {
			lo = n
		}
		if hi > n {
			hi = n
		}
		if hi < lo {
			hi = lo
		}
		out := []any{}
		i := lo
		for i < hi {
			out = append(out, t[i])
			i += 1
		}
		return out
	case *PyList:
		n := int64(len(t.Items))
		lo := __pytra_index(__pytra_int(lower), n)
		hi := __pytra_index(__pytra_int(upper), n)
		if lo < 0 {
			lo = 0
		}
		if hi < 0 {
			hi = 0
		}
		if lo > n {
			lo = n
		}
		if hi > n {
			hi = n
		}
		if hi < lo {
			hi = lo
		}
		out := []any{}
		i := lo
		for i < hi {
			out = append(out, t.Items[i])
			i += 1
		}
		return &PyList{Items: out}
	default:
		return nil
	}
}

func __pytra_isdigit(v any) bool {
	s := __pytra_str(v)
	if s == "" {
		return false
	}
	for _, ch := range s {
		if !unicode.IsDigit(ch) {
			return false
		}
	}
	return true
}

func __pytra_isalpha(v any) bool {
	s := __pytra_str(v)
	if s == "" {
		return false
	}
	for _, ch := range s {
		if !unicode.IsLetter(ch) {
			return false
		}
	}
	return true
}

func __pytra_contains(container any, value any) bool {
	switch t := container.(type) {
	case []any:
		i := 0
		for i < len(t) {
			if t[i] == value {
				return true
			}
			i += 1
		}
		return false
	case *PyList:
		i := 0
		for i < len(t.Items) {
			if t.Items[i] == value {
				return true
			}
			i += 1
		}
		return false
	case map[any]any:
		_, ok := t[value]
		return ok
	case string:
		needle := __pytra_str(value)
		return needle != "" && len(needle) <= len(t) && __pytra_str_contains(t, needle)
	default:
		return false
	}
}

func __pytra_str_contains(haystack string, needle string) bool {
	if needle == "" {
		return true
	}
	i := 0
	limit := len(haystack) - len(needle)
	for i <= limit {
		if haystack[i:i+len(needle)] == needle {
			return true
		}
		i += 1
	}
	return false
}

func __pytra_ifexp(cond bool, a any, b any) any {
	if cond {
		return a
	}
	return b
}

func __pytra_bytearray(init any) []any {
	out := []any{}
	switch t := init.(type) {
	case int:
		i := 0
		for i < t {
			out = append(out, int64(0))
			i += 1
		}
	case int64:
		i := int64(0)
		for i < t {
			out = append(out, int64(0))
			i += 1
		}
	case []any:
		i := 0
		for i < len(t) {
			out = append(out, t[i])
			i += 1
		}
	}
	return out
}

func __pytra_bytes(v any) []any {
	switch t := v.(type) {
	case []byte:
		out := []any{}
		i := 0
		for i < len(t) {
			out = append(out, int64(t[i]))
			i += 1
		}
		return out
	case []any:
		out := []any{}
		i := 0
		for i < len(t) {
			out = append(out, t[i])
			i += 1
		}
		return out
	case *PyList:
		out := []any{}
		i := 0
		for i < len(t.Items) {
			out = append(out, t.Items[i])
			i += 1
		}
		return out
	default:
		return []any{}
	}
}

func __pytra_list_repeat(value any, count any) *PyList {
	out := []any{}
	n := __pytra_int(count)
	i := int64(0)
	for i < n {
		out = append(out, value)
		i += 1
	}
	return &PyList{Items: out}
}

func __pytra_enumerate(v any) []any {
	var items []any
	switch t := v.(type) {
	case *PyList:
		items = t.Items
	default:
		items = __pytra_as_list(v)
	}
	out := []any{}
	i := int64(0)
	for i < int64(len(items)) {
		out = append(out, []any{i, items[i]})
		i += 1
	}
	return out
}

func __pytra_as_list(v any) []any {
	if t, ok := v.([]any); ok {
		return t
	}
	if t, ok := v.(*PyList); ok {
		return t.Items
	}
	if t, ok := v.(string); ok {
		// String iteration: split into individual characters
		runes := []rune(t)
		out := make([]any, len(runes))
		for i, r := range runes {
			out[i] = string(r)
		}
		return out
	}
	return []any{}
}

func __pytra_as_dict(v any) map[any]any {
	if t, ok := v.(map[any]any); ok {
		return t
	}
	return map[any]any{}
}

func __pytra_dict_get_default(container any, key any, defaultValue any) any {
	if t, ok := container.(map[any]any); ok {
		if v, exists := t[key]; exists {
			return v
		}
	}
	return defaultValue
}

// PNG/GIF functions removed: provided by utils_png.go / utils_gif.go
// generated from .east by linker when needed.

func __pytra_pop_last(v any) any {
	switch t := v.(type) {
	case *PyList:
		if len(t.Items) == 0 {
			return t
		}
		t.Items = t.Items[:len(t.Items)-1]
		return t
	case []any:
		if len(t) == 0 {
			return t
		}
		return t[:len(t)-1]
	default:
		return v
	}
}

func __pytra_print(args ...any) {
	if len(args) == 0 {
		fmt.Println()
		return
	}
	parts := make([]string, 0, len(args))
	for _, a := range args {
		parts = append(parts, pyToString(a))
	}
	fmt.Println(strings.Join(parts, " "))
}

func __pytra_min(a any, b any) any {
	af := __pytra_float(a)
	bf := __pytra_float(b)
	if af < bf {
		if __pytra_is_float(a) || __pytra_is_float(b) {
			return af
		}
		return __pytra_int(a)
	}
	if __pytra_is_float(a) || __pytra_is_float(b) {
		return bf
	}
	return __pytra_int(b)
}

func __pytra_max(a any, b any) any {
	af := __pytra_float(a)
	bf := __pytra_float(b)
	if af > bf {
		if __pytra_is_float(a) || __pytra_is_float(b) {
			return af
		}
		return __pytra_int(a)
	}
	if __pytra_is_float(a) || __pytra_is_float(b) {
		return bf
	}
	return __pytra_int(b)
}

func __pytra_is_int(v any) bool {
	switch v.(type) {
	case int, int64:
		return true
	default:
		return false
	}
}

func __pytra_is_float(v any) bool {
	_, ok := v.(float64)
	return ok
}

func __pytra_is_bool(v any) bool {
	_, ok := v.(bool)
	return ok
}

func __pytra_is_str(v any) bool {
	_, ok := v.(string)
	return ok
}

func __pytra_is_list(v any) bool {
	if _, ok := v.([]any); ok {
		return true
	}
	if _, ok := v.(*PyList); ok {
		return true
	}
	return false
}

func __pytra_as_int32(v any) int32 {
	return int32(__pytra_int(v))
}

func __pytra_as_uint8(v any) uint8 {
	return uint8(__pytra_int(v))
}

func __pytra_as_PyFile(v any) *PyFile {
	if f, ok := v.(PyFile); ok {
		return &f
	}
	if f, ok := v.(*PyFile); ok {
		return f
	}
	return nil
}
