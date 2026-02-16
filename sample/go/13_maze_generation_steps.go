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
const pytraEmbeddedSourceBase64 = "IyAxMzogREZT6L+36Lev55Sf5oiQ44Gu6YCy6KGM54q25rOB44KSR0lG5Ye65Yqb44GZ44KL44K144Oz44OX44Or44CCCgpmcm9tIF9fZnV0dXJlX18gaW1wb3J0IGFubm90YXRpb25zCgpmcm9tIHRpbWUgaW1wb3J0IHBlcmZfY291bnRlcgoKZnJvbSBweV9tb2R1bGUuZ2lmX2hlbHBlciBpbXBvcnQgZ3JheXNjYWxlX3BhbGV0dGUsIHNhdmVfZ2lmCgoKZGVmIGNhcHR1cmUoZ3JpZDogbGlzdFtsaXN0W2ludF1dLCB3OiBpbnQsIGg6IGludCwgc2NhbGU6IGludCkgLT4gYnl0ZXM6CiAgICB3aWR0aCA9IHcgKiBzY2FsZQogICAgaGVpZ2h0ID0gaCAqIHNjYWxlCiAgICBmcmFtZSA9IGJ5dGVhcnJheSh3aWR0aCAqIGhlaWdodCkKICAgIGZvciB5IGluIHJhbmdlKGgpOgogICAgICAgIGZvciB4IGluIHJhbmdlKHcpOgogICAgICAgICAgICB2ID0gMjU1IGlmIGdyaWRbeV1beF0gPT0gMCBlbHNlIDQwCiAgICAgICAgICAgIGZvciB5eSBpbiByYW5nZShzY2FsZSk6CiAgICAgICAgICAgICAgICBiYXNlID0gKHkgKiBzY2FsZSArIHl5KSAqIHdpZHRoICsgeCAqIHNjYWxlCiAgICAgICAgICAgICAgICBmb3IgeHggaW4gcmFuZ2Uoc2NhbGUpOgogICAgICAgICAgICAgICAgICAgIGZyYW1lW2Jhc2UgKyB4eF0gPSB2CiAgICByZXR1cm4gYnl0ZXMoZnJhbWUpCgoKZGVmIHJ1bl8xM19tYXplX2dlbmVyYXRpb25fc3RlcHMoKSAtPiBOb25lOgogICAgIyDlrp/ooYzmmYLplpPjgpLljYHliIbjgavnorrkv53jgZnjgovjgZ/jgoHjgIHov7fot6/jgrXjgqTjgrrjgajmj4/nlLvop6Plg4/luqbjgpLkuIrjgZLjgovjgIIKICAgIGNlbGxfdyA9IDg5CiAgICBjZWxsX2ggPSA2NwogICAgc2NhbGUgPSA1CiAgICBjYXB0dXJlX2V2ZXJ5ID0gMjAKICAgIG91dF9wYXRoID0gInNhbXBsZS9vdXQvMTNfbWF6ZV9nZW5lcmF0aW9uX3N0ZXBzLmdpZiIKCiAgICBzdGFydCA9IHBlcmZfY291bnRlcigpCiAgICBncmlkOiBsaXN0W2xpc3RbaW50XV0gPSBbXQogICAgZm9yIF8gaW4gcmFuZ2UoY2VsbF9oKToKICAgICAgICByb3c6IGxpc3RbaW50XSA9IFtdCiAgICAgICAgZm9yIF8gaW4gcmFuZ2UoY2VsbF93KToKICAgICAgICAgICAgcm93LmFwcGVuZCgxKQogICAgICAgIGdyaWQuYXBwZW5kKHJvdykKICAgIHN0YWNrOiBsaXN0W3R1cGxlW2ludCwgaW50XV0gPSBbKDEsIDEpXQogICAgZ3JpZFsxXVsxXSA9IDAKCiAgICBkaXJzOiBsaXN0W3R1cGxlW2ludCwgaW50XV0gPSBbKDIsIDApLCAoLTIsIDApLCAoMCwgMiksICgwLCAtMildCiAgICBmcmFtZXM6IGxpc3RbYnl0ZXNdID0gW10KICAgIHN0ZXAgPSAwCgogICAgd2hpbGUgbGVuKHN0YWNrKSA+IDA6CiAgICAgICAgbGFzdF9pbmRleCA9IGxlbihzdGFjaykgLSAxCiAgICAgICAgeCwgeSA9IHN0YWNrW2xhc3RfaW5kZXhdCiAgICAgICAgY2FuZGlkYXRlczogbGlzdFt0dXBsZVtpbnQsIGludCwgaW50LCBpbnRdXSA9IFtdCiAgICAgICAgZm9yIGsgaW4gcmFuZ2UoNCk6CiAgICAgICAgICAgIGR4LCBkeSA9IGRpcnNba10KICAgICAgICAgICAgbnggPSB4ICsgZHgKICAgICAgICAgICAgbnkgPSB5ICsgZHkKICAgICAgICAgICAgaWYgbnggPj0gMSBhbmQgbnggPCBjZWxsX3cgLSAxIGFuZCBueSA+PSAxIGFuZCBueSA8IGNlbGxfaCAtIDEgYW5kIGdyaWRbbnldW254XSA9PSAxOgogICAgICAgICAgICAgICAgaWYgZHggPT0gMjoKICAgICAgICAgICAgICAgICAgICBjYW5kaWRhdGVzLmFwcGVuZCgobngsIG55LCB4ICsgMSwgeSkpCiAgICAgICAgICAgICAgICBlbGlmIGR4ID09IC0yOgogICAgICAgICAgICAgICAgICAgIGNhbmRpZGF0ZXMuYXBwZW5kKChueCwgbnksIHggLSAxLCB5KSkKICAgICAgICAgICAgICAgIGVsaWYgZHkgPT0gMjoKICAgICAgICAgICAgICAgICAgICBjYW5kaWRhdGVzLmFwcGVuZCgobngsIG55LCB4LCB5ICsgMSkpCiAgICAgICAgICAgICAgICBlbHNlOgogICAgICAgICAgICAgICAgICAgIGNhbmRpZGF0ZXMuYXBwZW5kKChueCwgbnksIHgsIHkgLSAxKSkKCiAgICAgICAgaWYgbGVuKGNhbmRpZGF0ZXMpID09IDA6CiAgICAgICAgICAgIHN0YWNrLnBvcCgpCiAgICAgICAgZWxzZToKICAgICAgICAgICAgc2VsID0gY2FuZGlkYXRlc1soeCAqIDE3ICsgeSAqIDI5ICsgbGVuKHN0YWNrKSAqIDEzKSAlIGxlbihjYW5kaWRhdGVzKV0KICAgICAgICAgICAgbngsIG55LCB3eCwgd3kgPSBzZWwKICAgICAgICAgICAgZ3JpZFt3eV1bd3hdID0gMAogICAgICAgICAgICBncmlkW255XVtueF0gPSAwCiAgICAgICAgICAgIHN0YWNrLmFwcGVuZCgobngsIG55KSkKCiAgICAgICAgaWYgc3RlcCAlIGNhcHR1cmVfZXZlcnkgPT0gMDoKICAgICAgICAgICAgZnJhbWVzLmFwcGVuZChjYXB0dXJlKGdyaWQsIGNlbGxfdywgY2VsbF9oLCBzY2FsZSkpCiAgICAgICAgc3RlcCArPSAxCgogICAgZnJhbWVzLmFwcGVuZChjYXB0dXJlKGdyaWQsIGNlbGxfdywgY2VsbF9oLCBzY2FsZSkpCiAgICBzYXZlX2dpZihvdXRfcGF0aCwgY2VsbF93ICogc2NhbGUsIGNlbGxfaCAqIHNjYWxlLCBmcmFtZXMsIGdyYXlzY2FsZV9wYWxldHRlKCksIGRlbGF5X2NzPTQsIGxvb3A9MCkKICAgIGVsYXBzZWQgPSBwZXJmX2NvdW50ZXIoKSAtIHN0YXJ0CiAgICBwcmludCgib3V0cHV0OiIsIG91dF9wYXRoKQogICAgcHJpbnQoImZyYW1lczoiLCBsZW4oZnJhbWVzKSkKICAgIHByaW50KCJlbGFwc2VkX3NlYzoiLCBlbGFwc2VkKQoKCmlmIF9fbmFtZV9fID09ICJfX21haW5fXyI6CiAgICBydW5fMTNfbWF6ZV9nZW5lcmF0aW9uX3N0ZXBzKCkK"

// main は埋め込み Python を実行するエントリポイント。
func main() {
	os.Exit(pytraRunEmbeddedPython(pytraEmbeddedSourceBase64, os.Args[1:]))
}
