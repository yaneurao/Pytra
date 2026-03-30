// pathlib_native.go: @extern delegation for pytra.std.os_path.
// Hand-written native implementation.
package main

import (
	"os"
	"path/filepath"
)

func join(a string, b string) string {
	return filepath.Join(a, b)
}
func py_join(a string, b string) string { return join(a, b) }

func dirname(path string) string {
	return filepath.Dir(path)
}
func py_dirname(path string) string { return dirname(path) }

func basename(path string) string {
	return filepath.Base(path)
}
func py_basename(path string) string { return basename(path) }

func splitext(path string) []any {
	ext := filepath.Ext(path)
	if ext == "" {
		return []any{path, ""}
	}
	return []any{path[:len(path)-len(ext)], ext}
}
func py_splitext(path string) []any { return splitext(path) }

func abspath(path string) string {
	abs, err := filepath.Abs(path)
	if err != nil {
		panic(err)
	}
	return abs
}
func py_abspath(path string) string { return abspath(path) }

func exists(path string) bool {
	_, err := os.Stat(path)
	return err == nil
}
func py_exists(path string) bool { return exists(path) }

// Path is a Go analogue of Python's pathlib.Path.
type Path struct {
	_path string
}

func NewPath(s string) *Path {
	return &Path{_path: s}
}

func (p *Path) __pytra_is_Path() {}

func (p *Path) String() string {
	return p._path
}

func (p *Path) exists() bool {
	_, err := os.Stat(p._path)
	return err == nil
}

func (p *Path) resolve() *Path {
	abs, err := filepath.Abs(p._path)
	if err != nil {
		return p
	}
	return NewPath(abs)
}

func (p *Path) parent() *Path {
	return NewPath(filepath.Dir(p._path))
}

func (p *Path) parents() *PyList[*Path] {
	out := NewPyList[*Path]()
	cur := p._path
	for {
		parent := filepath.Dir(cur)
		if parent == cur {
			break
		}
		out.items = append(out.items, NewPath(parent))
		cur = parent
	}
	return out
}

func (p *Path) joinpath(parts ...string) *Path {
	result := p._path
	for _, part := range parts {
		result = filepath.Join(result, part)
	}
	return NewPath(result)
}

func (p *Path) name() string {
	return filepath.Base(p._path)
}

func (p *Path) stem() string {
	base := filepath.Base(p._path)
	ext := filepath.Ext(base)
	if ext == "" {
		return base
	}
	return base[:len(base)-len(ext)]
}

func (p *Path) suffix() string {
	return filepath.Ext(p._path)
}

func (p *Path) read_text(__opt_args ...string) string {
	data, err := os.ReadFile(p._path)
	if err != nil {
		panic(err)
	}
	return string(data)
}

func (p *Path) write_text(text string, __opt_args ...string) {
	err := os.WriteFile(p._path, []byte(text), 0644)
	if err != nil {
		panic(err)
	}
}

func (p *Path) mkdir(parents bool, exist_ok bool) {
	var err error
	if parents {
		err = os.MkdirAll(p._path, 0755)
	} else {
		err = os.Mkdir(p._path, 0755)
	}
	if err != nil && !exist_ok {
		panic(err)
	}
}

func (p *Path) glob(pattern string) *PyList[*Path] {
	full_pattern := filepath.Join(p._path, pattern)
	matches, err := filepath.Glob(full_pattern)
	out := NewPyList[*Path]()
	if err != nil {
		return out
	}
	for _, m := range matches {
		out.items = append(out.items, NewPath(m))
	}
	return out
}

func (p *Path) is_file() bool {
	info, err := os.Stat(p._path)
	return err == nil && !info.IsDir()
}

func (p *Path) is_dir() bool {
	info, err := os.Stat(p._path)
	return err == nil && info.IsDir()
}

func (p *Path) unlink() {
	os.Remove(p._path)
}

func (p *Path) with_suffix(new_suffix string) *Path {
	base := p._path
	ext := filepath.Ext(base)
	if ext != "" {
		base = base[:len(base)-len(ext)]
	}
	return NewPath(base + new_suffix)
}

func (p *Path) with_name(new_name string) *Path {
	dir := filepath.Dir(p._path)
	return NewPath(filepath.Join(dir, new_name))
}

func (p *Path) __str__() string {
	return p._path
}

func (p *Path) iterdir() *PyList[*Path] {
	entries, err := os.ReadDir(p._path)
	out := NewPyList[*Path]()
	if err != nil {
		return out
	}
	for _, e := range entries {
		out.items = append(out.items, NewPath(filepath.Join(p._path, e.Name())))
	}
	return out
}

func (p *Path) rglob(pattern string) *PyList[*Path] {
	out := NewPyList[*Path]()
	err := filepath.WalkDir(p._path, func(path string, d os.DirEntry, err error) error {
		if err != nil {
			return nil
		}
		matched, merr := filepath.Match(pattern, filepath.Base(path))
		if merr == nil && matched {
			out.items = append(out.items, NewPath(path))
		}
		return nil
	})
	_ = err
	return out
}

// py_str override for Path
func py_path_str(p *Path) string {
	if p == nil {
		return ""
	}
	return p._path
}
