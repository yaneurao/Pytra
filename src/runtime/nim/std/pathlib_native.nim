import std/os as std_os
import py_runtime

proc Path*(text: string): PyPath =
  text

proc Path*(value: PyObj): PyPath =
  py_str(value)

proc parent*(path: PyPath): PyPath =
  std_os.parentDir(path)

proc name*(path: PyPath): string =
  std_os.extractFilename(path)

proc stem*(path: PyPath): string =
  let (_, base, _) = std_os.splitFile(path)
  base

proc mkdir*(path: PyPath): void =
  std_os.createDir(path)

proc joinpath*(path: PyPath, child: string, more: varargs[string]): PyPath =
  result = std_os.joinPath(path, child)
  for part in more:
    result = std_os.joinPath(result, part)

proc `/`*(path: PyPath, child: string): PyPath =
  std_os.joinPath(path, child)

proc exists*(path: PyPath): bool =
  std_os.fileExists(path) or std_os.dirExists(path)

proc write_text*(path: PyPath, text: string): int =
  writeFile(path, text)
  text.len

proc read_text*(path: PyPath): string =
  readFile(path)

proc read_text*(path: PyPath, encoding: string): string =
  discard encoding
  readFile(path)
