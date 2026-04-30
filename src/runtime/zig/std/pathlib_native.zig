// Native implementation of pytra.std.pathlib for Zig.
//
// Provides Path type that works with Zig's []const u8 strings.
// This avoids the PyObject = i64 limitation for string-based types.
//
// source: src/pytra/std/pathlib.py

const std = @import("std");
const pytra = @import("../built_in/py_runtime.zig");
const os_native = @import("os_native.zig");
const os_path_native = @import("os_path_native.zig");

pub const Path = struct {
    _value: []const u8,

    pub fn init(value: anytype) Path {
        return Path{ ._value = pytra.union_as_str(value) };
    }

    pub fn cwd() *Path {
        const cwd_path = std.fs.cwd().realpathAlloc(std.heap.page_allocator, ".") catch ".";
        return pytra.make_object(Path, Path.init(cwd_path));
    }

    pub fn __str__(self: *const Path) []const u8 {
        return self._value;
    }

    pub fn __repr__(self: *const Path) []const u8 {
        _ = self;
        return "Path(...)";
    }

    pub fn __fspath__(self: *const Path) []const u8 {
        return self._value;
    }

    pub fn __truediv__(self: *const Path, rhs: []const u8) *Path {
        return pytra.make_object(Path, Path.init(os_path_native.join(self._value, rhs)));
    }

    pub fn parent(self: *const Path) *Path {
        const d = os_path_native.dirname(self._value);
        const result = if (d.len == 0) "." else d;
        return pytra.make_object(Path, Path.init(result));
    }

    pub fn name(self: *const Path) []const u8 {
        return os_path_native.basename(self._value);
    }

    pub fn suffix(self: *const Path) []const u8 {
        const bn = os_path_native.basename(self._value);
        if (std.mem.lastIndexOfScalar(u8, bn, '.')) |dot| {
            return bn[dot..];
        }
        return "";
    }

    pub fn stem(self: *const Path) []const u8 {
        const bn = os_path_native.basename(self._value);
        if (std.mem.lastIndexOfScalar(u8, bn, '.')) |dot| {
            return bn[0..dot];
        }
        return bn;
    }

    pub fn exists(self: *const Path) bool {
        return os_path_native.exists(self._value);
    }

    pub fn mkdir(self: *const Path) void {
        os_native.makedirs(self._value, true);
    }

    pub fn read_text(self: *const Path) []const u8 {
        const file = std.fs.cwd().openFile(self._value, .{}) catch return "";
        defer file.close();
        return file.readToEndAlloc(std.heap.page_allocator, 1 << 20) catch "";
    }

    pub fn write_text(self: *const Path, text: []const u8) void {
        const f = std.fs.cwd().createFile(self._value, .{}) catch return;
        defer f.close();
        f.writeAll(text) catch {};
    }

    pub fn resolve(self: *const Path) *Path {
        return pytra.make_object(Path, Path.init(self._value));
    }

    pub fn joinpath(self: *const Path, rhs: []const u8) *Path {
        return pytra.make_object(Path, Path.init(os_path_native.join(self._value, rhs)));
    }
};
