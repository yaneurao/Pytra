const std = @import("std");
const pytra = @import("../built_in/py_runtime.zig");

var argv_store: pytra.Obj = pytra.empty_list();
var path_store: pytra.Obj = pytra.empty_list();

pub const argv: pytra.Obj = argv_store;
pub const path: pytra.Obj = path_store;
pub const stderr: []const u8 = "stderr";
pub const stdout: []const u8 = "stdout";

pub fn exit(code: i64) void {
    std.process.exit(@intCast(code));
}

pub fn set_argv(values: pytra.Obj) void {
    argv_store = values;
}

pub fn set_path(values: pytra.Obj) void {
    path_store = values;
}

pub fn write_stderr(text: []const u8) void {
    std.io.getStdErr().writer().writeAll(text) catch {};
}

pub fn write_stdout(text: []const u8) void {
    std.io.getStdOut().writer().writeAll(text) catch {};
}
