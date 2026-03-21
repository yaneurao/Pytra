// Pytra Zig runtime – minimal built-in helpers.
// This file is loaded by generated Zig programs via @import("py_runtime.zig").

const std = @import("std");

/// Print a single value followed by newline, Python-style.
pub fn print(value: anytype) void {
    const writer = std.io.getStdOut().writer();
    printValue(writer, value);
    writer.writeAll("\n") catch {};
}

/// Print two values separated by a space.
pub fn print2(a: anytype, b: anytype) void {
    const writer = std.io.getStdOut().writer();
    printValue(writer, a);
    writer.writeAll(" ") catch {};
    printValue(writer, b);
    writer.writeAll("\n") catch {};
}

/// Print three values separated by spaces.
pub fn print3(a: anytype, b: anytype, c: anytype) void {
    const writer = std.io.getStdOut().writer();
    printValue(writer, a);
    writer.writeAll(" ") catch {};
    printValue(writer, b);
    writer.writeAll(" ") catch {};
    printValue(writer, c);
    writer.writeAll("\n") catch {};
}

fn printValue(writer: anytype, value: anytype) void {
    const T = @TypeOf(value);
    switch (@typeInfo(T)) {
        .Int, .ComptimeInt => {
            writer.print("{d}", .{value}) catch {};
        },
        .Float, .ComptimeFloat => {
            printFloat(writer, value);
        },
        .Bool => {
            writer.writeAll(if (value) "True" else "False") catch {};
        },
        .Pointer => |ptr_info| {
            if (ptr_info.size == .Slice and ptr_info.child == u8) {
                writer.writeAll(value) catch {};
            } else {
                writer.print("{any}", .{value}) catch {};
            }
        },
        .Optional => {
            if (value) |v| {
                printValue(writer, v);
            } else {
                writer.writeAll("None") catch {};
            }
        },
        .Null => {
            writer.writeAll("None") catch {};
        },
        .Void => {
            writer.writeAll("None") catch {};
        },
        else => {
            writer.print("{any}", .{value}) catch {};
        },
    }
}

fn printFloat(writer: anytype, value: anytype) void {
    // Python-style float printing: no trailing zeros, but at least one decimal
    const v: f64 = @floatCast(value);
    // Check if it's an integer value
    const truncated = @trunc(v);
    if (v == truncated and !std.math.isNan(v) and !std.math.isInf(v)) {
        writer.print("{d}.0", .{@as(i64, @intFromFloat(truncated))}) catch {};
    } else {
        writer.print("{d}", .{v}) catch {};
    }
}

/// Python-style truthiness check.
pub fn truthy(value: anytype) bool {
    const T = @TypeOf(value);
    switch (@typeInfo(T)) {
        .Bool => return value,
        .Int, .ComptimeInt => return value != 0,
        .Float, .ComptimeFloat => return value != 0.0,
        .Optional => return value != null,
        .Null => return false,
        .Pointer => |ptr_info| {
            if (ptr_info.size == .Slice) {
                return value.len > 0;
            }
            return true;
        },
        else => return true,
    }
}

/// Convert a value to string representation (stub).
pub fn to_str(value: anytype) []const u8 {
    _ = value;
    return "<value>";
}

/// Concatenate two strings (stub).
pub fn str_concat(a: []const u8, b: []const u8) []const u8 {
    _ = a;
    _ = b;
    return "<concat>";
}

/// Join multiple strings (stub).
pub fn str_join(parts: anytype) []const u8 {
    _ = parts;
    return "<join>";
}

/// Create a new empty dict (stub).
pub fn new_dict() void {
    return;
}

/// isinstance check (stub).
pub fn isinstance_check(obj: anytype, typ: anytype) bool {
    _ = obj;
    _ = typ;
    return false;
}

/// Contains check (stub for `in` operator).
pub fn contains(haystack: anytype, needle: anytype) bool {
    _ = haystack;
    _ = needle;
    return false;
}

/// Reference-counted object wrapper (Pytra Object<T> equivalent).
pub fn Object(comptime T: type) type {
    return struct {
        const Self = @This();
        ptr: *T,
        rc: *usize,

        pub fn init(value: T) Self {
            const alloc = std.heap.page_allocator;
            const p = alloc.create(T) catch @panic("alloc failed");
            p.* = value;
            const rc = alloc.create(usize) catch @panic("alloc failed");
            rc.* = 1;
            return Self{ .ptr = p, .rc = rc };
        }

        pub fn clone(self: Self) Self {
            self.rc.* += 1;
            return Self{ .ptr = self.ptr, .rc = self.rc };
        }

        pub fn release(self: Self) void {
            self.rc.* -= 1;
            if (self.rc.* == 0) {
                const alloc = std.heap.page_allocator;
                alloc.destroy(self.ptr);
                alloc.destroy(self.rc);
            }
        }
    };
}

/// Create a heap-allocated object and return a pointer.
pub fn make_object(comptime T: type, value: T) *T {
    const alloc = std.heap.page_allocator;
    const p = alloc.create(T) catch @panic("alloc failed");
    p.* = value;
    return p;
}

/// Empty list (stub for comprehensions).
pub fn empty_list() void {
    return;
}

/// Slice (stub).
pub fn slice(lower: anytype, upper: anytype) void {
    _ = lower;
    _ = upper;
    return;
}
