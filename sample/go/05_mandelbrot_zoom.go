// このファイルは自動生成です（Python -> Go embedded mode）。

// Python 埋め込み実行向けの Go ランタイム補助。
// 生成された Go コードから呼び出し、Python ソースを一時ファイルに展開して実行する。

package main

import (
	"encoding/base64"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
)

// pytraRunEmbeddedPython は、Base64 で埋め込まれた Python ソースを実行する。
//
// Args:
//   sourceBase64: 埋め込み Python ソースコード（Base64 文字列）。
//   args: Python スクリプトへ渡す引数。
//
// Returns:
//   Python プロセスの終了コード。異常時は 1 を返す。
func pytraRunEmbeddedPython(sourceBase64 string, args []string) int {
	sourceBytes, decodeErr := base64.StdEncoding.DecodeString(sourceBase64)
	if decodeErr != nil {
		fmt.Fprintln(os.Stderr, "error: failed to decode embedded python source")
		return 1
	}

	tempDir, mkErr := os.MkdirTemp("", "pytra_go_")
	if mkErr != nil {
		fmt.Fprintln(os.Stderr, "error: failed to create temp directory")
		return 1
	}
	defer os.RemoveAll(tempDir)

	scriptPath := filepath.Join(tempDir, "embedded.py")
	if writeErr := os.WriteFile(scriptPath, sourceBytes, 0o600); writeErr != nil {
		fmt.Fprintln(os.Stderr, "error: failed to write temp python script")
		return 1
	}

	pythonPath := "src"
	if current, ok := os.LookupEnv("PYTHONPATH"); ok && current != "" {
		pythonPath = pythonPath + string(os.PathListSeparator) + current
	}

	run := func(interpreter string) (int, error) {
		cmd := exec.Command(interpreter, append([]string{scriptPath}, args...)...)
		cmd.Stdout = os.Stdout
		cmd.Stderr = os.Stderr
		cmd.Stdin = os.Stdin
		env := os.Environ()
		env = append(env, "PYTHONPATH="+pythonPath)
		cmd.Env = env
		err := cmd.Run()
		if err == nil {
			return 0, nil
		}
		if exitErr, ok := err.(*exec.ExitError); ok {
			return exitErr.ExitCode(), nil
		}
		return 0, err
	}

	if code, err := run("python3"); err == nil {
		return code
	}
	if code, err := run("python"); err == nil {
		return code
	}

	fmt.Fprintln(os.Stderr, "error: python interpreter not found (python3/python)")
	return 1
}

// 埋め込み Python ソース（Base64）。
const pytraEmbeddedSourceBase64 = "IyAwNTog44Oe44Oz44OH44Or44OW44Ot6ZuG5ZCI44K644O844Og44KS44Ki44OL44Oh44O844K344On44OzR0lG44Go44GX44Gm5Ye65Yqb44GZ44KL44K144Oz44OX44Or44CCCgpmcm9tIF9fZnV0dXJlX18gaW1wb3J0IGFubm90YXRpb25zCgpmcm9tIHRpbWUgaW1wb3J0IHBlcmZfY291bnRlcgoKZnJvbSBweV9tb2R1bGUuZ2lmX2hlbHBlciBpbXBvcnQgZ3JheXNjYWxlX3BhbGV0dGUsIHNhdmVfZ2lmCgoKZGVmIHJlbmRlcl9mcmFtZSh3aWR0aDogaW50LCBoZWlnaHQ6IGludCwgY2VudGVyX3g6IGZsb2F0LCBjZW50ZXJfeTogZmxvYXQsIHNjYWxlOiBmbG9hdCwgbWF4X2l0ZXI6IGludCkgLT4gYnl0ZXM6CiAgICBmcmFtZSA9IGJ5dGVhcnJheSh3aWR0aCAqIGhlaWdodCkKICAgIGlkeCA9IDAKICAgIGZvciB5IGluIHJhbmdlKGhlaWdodCk6CiAgICAgICAgY3kgPSBjZW50ZXJfeSArICh5IC0gaGVpZ2h0ICogMC41KSAqIHNjYWxlCiAgICAgICAgZm9yIHggaW4gcmFuZ2Uod2lkdGgpOgogICAgICAgICAgICBjeCA9IGNlbnRlcl94ICsgKHggLSB3aWR0aCAqIDAuNSkgKiBzY2FsZQogICAgICAgICAgICB6eCA9IDAuMAogICAgICAgICAgICB6eSA9IDAuMAogICAgICAgICAgICBpID0gMAogICAgICAgICAgICB3aGlsZSBpIDwgbWF4X2l0ZXI6CiAgICAgICAgICAgICAgICB6eDIgPSB6eCAqIHp4CiAgICAgICAgICAgICAgICB6eTIgPSB6eSAqIHp5CiAgICAgICAgICAgICAgICBpZiB6eDIgKyB6eTIgPiA0LjA6CiAgICAgICAgICAgICAgICAgICAgYnJlYWsKICAgICAgICAgICAgICAgIHp5ID0gMi4wICogenggKiB6eSArIGN5CiAgICAgICAgICAgICAgICB6eCA9IHp4MiAtIHp5MiArIGN4CiAgICAgICAgICAgICAgICBpICs9IDEKICAgICAgICAgICAgZnJhbWVbaWR4XSA9IGludCgoMjU1LjAgKiBpKSAvIG1heF9pdGVyKQogICAgICAgICAgICBpZHggKz0gMQogICAgcmV0dXJuIGJ5dGVzKGZyYW1lKQoKCmRlZiBydW5fMDVfbWFuZGVsYnJvdF96b29tKCkgLT4gTm9uZToKICAgIHdpZHRoID0gMzIwCiAgICBoZWlnaHQgPSAyNDAKICAgIGZyYW1lX2NvdW50ID0gNDgKICAgIG1heF9pdGVyID0gMTEwCiAgICBjZW50ZXJfeCA9IC0wLjc0MzY0Mzg4NzAzNzE1MQogICAgY2VudGVyX3kgPSAwLjEzMTgyNTkwNDIwNTMzCiAgICBiYXNlX3NjYWxlID0gMy4yIC8gd2lkdGgKICAgIHpvb21fcGVyX2ZyYW1lID0gMC45MwogICAgb3V0X3BhdGggPSAic2FtcGxlL291dC8wNV9tYW5kZWxicm90X3pvb20uZ2lmIgoKICAgIHN0YXJ0ID0gcGVyZl9jb3VudGVyKCkKICAgIGZyYW1lczogbGlzdFtieXRlc10gPSBbXQogICAgc2NhbGUgPSBiYXNlX3NjYWxlCiAgICBmb3IgXyBpbiByYW5nZShmcmFtZV9jb3VudCk6CiAgICAgICAgZnJhbWVzLmFwcGVuZChyZW5kZXJfZnJhbWUod2lkdGgsIGhlaWdodCwgY2VudGVyX3gsIGNlbnRlcl95LCBzY2FsZSwgbWF4X2l0ZXIpKQogICAgICAgIHNjYWxlICo9IHpvb21fcGVyX2ZyYW1lCgogICAgc2F2ZV9naWYob3V0X3BhdGgsIHdpZHRoLCBoZWlnaHQsIGZyYW1lcywgZ3JheXNjYWxlX3BhbGV0dGUoKSwgZGVsYXlfY3M9NSwgbG9vcD0wKQogICAgZWxhcHNlZCA9IHBlcmZfY291bnRlcigpIC0gc3RhcnQKICAgIHByaW50KCJvdXRwdXQ6Iiwgb3V0X3BhdGgpCiAgICBwcmludCgiZnJhbWVzOiIsIGZyYW1lX2NvdW50KQogICAgcHJpbnQoImVsYXBzZWRfc2VjOiIsIGVsYXBzZWQpCgoKaWYgX19uYW1lX18gPT0gIl9fbWFpbl9fIjoKICAgIHJ1bl8wNV9tYW5kZWxicm90X3pvb20oKQo="

// main は埋め込み Python を実行するエントリポイント。
func main() {
	os.Exit(pytraRunEmbeddedPython(pytraEmbeddedSourceBase64, os.Args[1:]))
}
