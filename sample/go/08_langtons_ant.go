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
const pytraEmbeddedSourceBase64 = "IyAwODog44Op44Oz44Kw44OI44Oz44Gu44Ki44Oq44Gu6LuM6Leh44KSR0lG5Ye65Yqb44GZ44KL44K144Oz44OX44Or44CCCgpmcm9tIF9fZnV0dXJlX18gaW1wb3J0IGFubm90YXRpb25zCgpmcm9tIHRpbWUgaW1wb3J0IHBlcmZfY291bnRlcgoKZnJvbSBweV9tb2R1bGUuZ2lmX2hlbHBlciBpbXBvcnQgZ3JheXNjYWxlX3BhbGV0dGUsIHNhdmVfZ2lmCgoKZGVmIGNhcHR1cmUoZ3JpZDogbGlzdFtsaXN0W2ludF1dLCB3OiBpbnQsIGg6IGludCkgLT4gYnl0ZXM6CiAgICBmcmFtZSA9IGJ5dGVhcnJheSh3ICogaCkKICAgIGkgPSAwCiAgICBmb3IgeSBpbiByYW5nZShoKToKICAgICAgICBmb3IgeCBpbiByYW5nZSh3KToKICAgICAgICAgICAgZnJhbWVbaV0gPSAyNTUgaWYgZ3JpZFt5XVt4XSBlbHNlIDAKICAgICAgICAgICAgaSArPSAxCiAgICByZXR1cm4gYnl0ZXMoZnJhbWUpCgoKZGVmIHJ1bl8wOF9sYW5ndG9uc19hbnQoKSAtPiBOb25lOgogICAgdyA9IDQyMAogICAgaCA9IDQyMAogICAgb3V0X3BhdGggPSAic2FtcGxlL291dC8wOF9sYW5ndG9uc19hbnQuZ2lmIgoKICAgIHN0YXJ0ID0gcGVyZl9jb3VudGVyKCkKCiAgICBncmlkOiBsaXN0W2xpc3RbaW50XV0gPSBbXQogICAgZm9yIGd5IGluIHJhbmdlKGgpOgogICAgICAgIHJvdzogbGlzdFtpbnRdID0gW10KICAgICAgICBmb3IgZ3ggaW4gcmFuZ2Uodyk6CiAgICAgICAgICAgIHJvdy5hcHBlbmQoMCkKICAgICAgICBncmlkLmFwcGVuZChyb3cpCiAgICB4ID0gdyAvLyAyCiAgICB5ID0gaCAvLyAyCiAgICBkID0gMAoKICAgIHN0ZXBzX3RvdGFsID0gNjAwMDAwCiAgICBjYXB0dXJlX2V2ZXJ5ID0gMzAwMAogICAgZnJhbWVzOiBsaXN0W2J5dGVzXSA9IFtdCgogICAgZm9yIGkgaW4gcmFuZ2Uoc3RlcHNfdG90YWwpOgogICAgICAgIGlmIGdyaWRbeV1beF0gPT0gMDoKICAgICAgICAgICAgZCA9IChkICsgMSkgJSA0CiAgICAgICAgICAgIGdyaWRbeV1beF0gPSAxCiAgICAgICAgZWxzZToKICAgICAgICAgICAgZCA9IChkICsgMykgJSA0CiAgICAgICAgICAgIGdyaWRbeV1beF0gPSAwCgogICAgICAgIGlmIGQgPT0gMDoKICAgICAgICAgICAgeSA9ICh5IC0gMSArIGgpICUgaAogICAgICAgIGVsaWYgZCA9PSAxOgogICAgICAgICAgICB4ID0gKHggKyAxKSAlIHcKICAgICAgICBlbGlmIGQgPT0gMjoKICAgICAgICAgICAgeSA9ICh5ICsgMSkgJSBoCiAgICAgICAgZWxzZToKICAgICAgICAgICAgeCA9ICh4IC0gMSArIHcpICUgdwoKICAgICAgICBpZiBpICUgY2FwdHVyZV9ldmVyeSA9PSAwOgogICAgICAgICAgICBmcmFtZXMuYXBwZW5kKGNhcHR1cmUoZ3JpZCwgdywgaCkpCgogICAgc2F2ZV9naWYob3V0X3BhdGgsIHcsIGgsIGZyYW1lcywgZ3JheXNjYWxlX3BhbGV0dGUoKSwgZGVsYXlfY3M9NSwgbG9vcD0wKQogICAgZWxhcHNlZCA9IHBlcmZfY291bnRlcigpIC0gc3RhcnQKICAgIHByaW50KCJvdXRwdXQ6Iiwgb3V0X3BhdGgpCiAgICBwcmludCgiZnJhbWVzOiIsIGxlbihmcmFtZXMpKQogICAgcHJpbnQoImVsYXBzZWRfc2VjOiIsIGVsYXBzZWQpCgoKaWYgX19uYW1lX18gPT0gIl9fbWFpbl9fIjoKICAgIHJ1bl8wOF9sYW5ndG9uc19hbnQoKQo="

// main は埋め込み Python を実行するエントリポイント。
func main() {
	os.Exit(pytraRunEmbeddedPython(pytraEmbeddedSourceBase64, os.Args[1:]))
}
