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
