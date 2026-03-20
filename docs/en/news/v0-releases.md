# v0 Release Series (Past News)

## 2026-03-20 | v0.15.0 Released

> Version 0.15.0 released. PowerShell is now supported as a backend.

## 2026-03-18 | v0.14.0 Released

> Version 0.14.0 released. [Recursive union types](../../ja/spec/spec-tagged-union.md) (`type X = A | B | ...`) are now supported.

## 2026-03-11 | v0.13.0 Released

> Version 0.13.0 released. A NES (Famicom) emulator written in Python + SDL3 now works. [Super Mario Bros. 3 runs on it](https://x.com/yaneuraou/status/2031612549658202538), though very slowly. We are currently improving Pytra so it can transpile this emulator to C++.

## 2026-03-10 | v0.12.0 Released

> Version 0.12.0 was released. I am currently in the middle of a large runtime reorganization.

## 2026-03-09 | v0.11.0 Released

> Version 0.11.0 was released. We are revisiting object boundaries, and the tutorial has been improved.

## 2026-03-08 | v0.10.0 Released

> Version 0.10.0 was released. `@template` is now available, and runtime support for each target language is currently being refined.

## 2026-03-07 | v0.9.0 Released

> Version 0.9.0 was released. The large-scale refactor is complete, and all target languages are usable again. `@extern` and `@abi` are now available, so transpiled code can now be called from other languages as well.

## 2026-03-06 | v0.8.0 Released

> Version 0.8.0 was released. The ABI boundary is being redefined, and a large-scale refactor is in progress. At the moment, backends other than the C++ transpiler are broken, so please use v0.7.0.

## 2026-03-04 | v0.7.0 Released

> Version 0.7.0 was released, adding PHP as a supported target language. Nim official support is in progress, followed by Julia and Dart.

## 2026-03-02 | v0.6.0 Released

> Version 0.6.0 was released, adding Scala as a supported target language.

## 2026-03-01 | v0.5.0 Released

> Version 0.5.0 was released, adding Lua as a supported target language.

## 2026-02-28 | v0.4.0 Released

> Version 0.4.0 was released, adding Ruby as a supported target language.

## 2026-02-27 | v0.3.0 Released

> Version 0.3.0 reorganizes EAST (intermediate representation) into staged processing (`EAST1 -> EAST2 -> EAST3`) and performs a large-scale split/slimming of the C++ CodeEmitter.

## 2026-02-25 | v0.2.0 Released

> Version 0.2.0 was released. Outputs for all languages now stay closer to the original source code.

## 2026-02-23 | v0.1.0 Released

> Pytra can now generate more readable C++ code in a style that stays very close to the original Python source.
