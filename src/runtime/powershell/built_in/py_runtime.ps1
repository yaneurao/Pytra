Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Built-in exception base constructors
function Exception { param($self, $msg = ""); $self["__type__"] = "Exception"; $self["__msg__"] = if ($msg -eq $null) { "" } else { [string]$msg } }
function BaseException { param($self, $msg = ""); Exception $self $msg; $self["__type__"] = "BaseException" }
function ValueError { param($self, $msg = ""); Exception $self $msg; $self["__type__"] = "ValueError" }
function TypeError { param($self, $msg = ""); Exception $self $msg; $self["__type__"] = "TypeError" }
function RuntimeError { param($self, $msg = ""); Exception $self $msg; $self["__type__"] = "RuntimeError" }
function KeyError { param($self, $msg = ""); Exception $self $msg; $self["__type__"] = "KeyError" }
function IndexError { param($self, $msg = ""); Exception $self $msg; $self["__type__"] = "IndexError" }
function AttributeError { param($self, $msg = ""); Exception $self $msg; $self["__type__"] = "AttributeError" }
function NotImplementedError { param($self, $msg = ""); Exception $self $msg; $self["__type__"] = "NotImplementedError" }
function StopIteration { param($self, $msg = ""); Exception $self $msg; $self["__type__"] = "StopIteration" }
function OverflowError { param($self, $msg = ""); Exception $self $msg; $self["__type__"] = "OverflowError" }
function ZeroDivisionError { param($self, $msg = ""); Exception $self $msg; $self["__type__"] = "ZeroDivisionError" }
function OSError { param($self, $msg = ""); Exception $self $msg; $self["__type__"] = "OSError" }
function IOError { param($self, $msg = ""); Exception $self $msg; $self["__type__"] = "IOError" }
function FileNotFoundError { param($self, $msg = ""); Exception $self $msg; $self["__type__"] = "FileNotFoundError" }

function __pytra_print {
    if ($args.Count -eq 0) {
        [Console]::Out.WriteLine("")
        return
    }
    $parts = New-Object System.Collections.Generic.List[string]
    foreach ($item in $args) {
        $parts.Add((__pytra_str $item))
    }
    [Console]::Out.WriteLine(($parts -join " "))
}

function __pytra_len {
    param([object]$value)
    if ($value -eq $null) { return 0 }
    if ($value -is [string]) { return $value.Length }
    if ($value -is [array]) { return $value.Length }
    if ($value -is [System.Collections.ICollection]) { return $value.Count }
    return 0
}

function __pytra_repr {
    param([object]$value)
    if ($value -eq $null) { return "None" }
    if ($value -is [bool]) { return $(if ($value) { "True" } else { "False" }) }
    if ($value -is [string]) { return "'" + $value.Replace("\", "\\").Replace("'", "\'") + "'" }
    # array (PS1 native array) → tuple repr (a, b) or (a,)
    if ($value -is [array]) {
        $parts2 = [System.Collections.Generic.List[string]]::new()
        foreach ($item in $value) { $parts2.Add((__pytra_repr $item)) }
        if ($parts2.Count -eq 1) { return "(" + $parts2[0] + ",)" }
        return "(" + ($parts2 -join ", ") + ")"
    }
    # IList (List[object]) → list repr [a, b]
    if ($value -is [System.Collections.IList]) {
        $parts2 = [System.Collections.Generic.List[string]]::new()
        foreach ($item in $value) { $parts2.Add((__pytra_repr $item)) }
        return "[" + ($parts2 -join ", ") + "]"
    }
    # hashtable → dict repr {'k': v} or class __str__
    if ($value -is [hashtable]) {
        if ($value.ContainsKey("__type__")) { return (__pytra_str $value) }
        $parts2 = [System.Collections.Generic.List[string]]::new()
        foreach ($k in ($value.Keys | Sort-Object)) { $parts2.Add((__pytra_repr $k) + ": " + (__pytra_repr $value[$k])) }
        return "{" + ($parts2 -join ", ") + "}"
    }
    return (__pytra_str $value)
}

function __pytra_str {
    param([object]$value)
    if ($value -eq $null) { return "None" }
    if ($value -is [bool]) { return $(if ($value) { "True" } else { "False" }) }
    # array (PS1 native array) → tuple repr
    if ($value -is [array]) {
        $parts2 = [System.Collections.Generic.List[string]]::new()
        foreach ($item in $value) { $parts2.Add((__pytra_repr $item)) }
        if ($parts2.Count -eq 1) { return "(" + $parts2[0] + ",)" }
        return "(" + ($parts2 -join ", ") + ")"
    }
    # IList (List[object]) → list repr
    if ($value -is [System.Collections.IList]) {
        $parts2 = [System.Collections.Generic.List[string]]::new()
        foreach ($item in $value) { $parts2.Add((__pytra_repr $item)) }
        return "[" + ($parts2 -join ", ") + "]"
    }
    # Hashtable-based class with __str__ method
    if ($value -is [hashtable] -and $value.ContainsKey("__type__")) {
        $tn = $value["__type__"]
        $str_fn = $tn + "___str__"
        if (Get-Command $str_fn -ErrorAction SilentlyContinue) {
            return [string](& (Get-Command $str_fn) $value)
        }
        # Exception-like: return __msg__ if present
        if ($value.ContainsKey("__msg__")) { return [string]$value["__msg__"] }
    }
    # Plain hashtable → dict repr (sorted keys for determinism)
    if ($value -is [hashtable]) {
        $parts2 = [System.Collections.Generic.List[string]]::new()
        foreach ($k in ($value.Keys | Sort-Object)) { $parts2.Add((__pytra_repr $k) + ": " + (__pytra_repr $value[$k])) }
        return "{" + ($parts2 -join ", ") + "}"
    }
    if ($value -is [double] -or $value -is [float]) {
        if ([double]::IsNaN($value)) { return "nan" }
        if ([double]::IsPositiveInfinity($value)) { return "inf" }
        if ([double]::IsNegativeInfinity($value)) { return "-inf" }
        $sv = $value.ToString("R").ToLower()
        if ($sv -notmatch '\.' -and $sv -notmatch 'e') { $sv = $sv + ".0" }
        return $sv
    }
    return [string]$value
}

function __pytra_int {
    param([object]$value)
    if ($value -eq $null) { return 0 }
    if ($value -is [bool]) { return $(if ($value) { 1 } else { 0 }) }
    if ($value -is [double] -or $value -is [float] -or $value -is [decimal]) {
        # Python int() truncates toward zero (like C cast), not rounds
        return [long][Math]::Truncate([double]$value)
    }
    try {
        return [long]$value
    } catch {
        return 0
    }
}

function __pytra_bytearray {
    param([object]$size = 0)
    # Return List[object] for in-place .Add() support (mutable like Python bytearray)
    if ($size -is [array] -or $size -is [System.Collections.IList]) {
        $result = [System.Collections.Generic.List[object]]::new()
        foreach ($item in $size) {
            [void]$result.Add((__pytra_int $item))
        }
        return ,$result
    }
    $count = __pytra_int $size
    if ($count -lt 0) {
        throw "[PowerShell backend experimental] negative bytearray size"
    }
    if ($count -eq 0) {
        # Empty bytearray: return List for .Add() / .AddRange() support
        return ,([System.Collections.Generic.List[object]]::new())
    }
    $result = [System.Collections.Generic.List[object]]::new()
    for ($i = 0; $i -lt $count; $i++) {
        [void]$result.Add(0)
    }
    return ,$result
}

function __pytra_bytes {
    param([object]$value)
    if ($value -is [string]) {
        $result = New-Object System.Collections.Generic.List[int]
        foreach ($ch in $value.ToCharArray()) {
            [void]$result.Add([int][char]$ch)
        }
        return [int[]]$result
    }
    if ($value -is [System.Array]) {
        # Already a PS1 native array (e.g. bytes passed to bytes()), return as-is.
        return $value
    }
    if ($value -is [System.Collections.Generic.List[object]]) {
        # Fast path for bytearray: elements are already integers from __pytra_bytearray.
        # ToArray() avoids per-element __pytra_int function calls (major speedup for GIF frames).
        return $value.ToArray()
    }
    if ($value -is [System.Collections.ICollection]) {
        $result = [System.Collections.Generic.List[object]]::new()
        foreach ($item in $value) {
            [void]($result.Add((__pytra_int $item)))
        }
        return $result.ToArray()
    }
    if ($value -is [int] -or $value -is [long]) {
        return __pytra_bytearray $value
    }
    return @()
}

function __pytra_ord {
    param([object]$value)
    if ($value -is [char]) { return [int]$value }
    if ($value -isnot [string] -or $value.Length -eq 0) {
        throw "[PowerShell backend experimental] ord() expected a non-empty string"
    }
    return [int][char]$value[0]
}

function __pytra_chr {
    param([object]$value)
    $codepoint = __pytra_int $value
    if ($codepoint -lt 0 -or $codepoint -gt 0x10FFFF) {
        throw "[PowerShell backend experimental] chr() argument out of range"
    }
    return [string]([char]$codepoint)
}

function __pytra_list {
    param([object]$value = 0)
    if ($value -is [int] -or $value -is [long]) {
        $count = __pytra_int $value
        $result = [System.Collections.Generic.List[object]]::new()
        for ($i = 0; $i -lt $count; $i++) {
            [void]$result.Add($null)
        }
        return ,$result
    }
    if ($value -is [System.Collections.ICollection]) {
        $result = [System.Collections.Generic.List[object]]::new()
        foreach ($item in $value) {
            [void]$result.Add($item)
        }
        return ,$result
    }
    return @()
}

function __pytra_mklist {
    # Construct a List[object] from individual arguments, preserving arrays as elements.
    # Unlike [List]@(elem1, elem2), this avoids PS1's @() flattening of inner arrays.
    $result = [System.Collections.Generic.List[object]]::new()
    foreach ($elem in $args) {
        [void]($result.Add($elem))
    }
    return ,$result
}

function __pytra_set_key {
    param([object]$item)
    if ($item -is [System.Array]) {
        $parts = foreach ($e in $item) {
            if ($e -is [System.Array]) { (__pytra_set_key $e) } else { [string]$e }
        }
        return "(__t__:" + ($parts -join ",") + ")"
    }
    return $item
}

function __pytra_set {
    param([object[]]$values)
    $result = @{}
    $all_values = @()
    if ($values -ne $null) { $all_values += @($values) }
    if ($args -ne $null) { $all_values += @($args) }
    foreach ($item in $all_values) {
        $result[(__pytra_set_key $item)] = $true
    }
    return $result
}

function __pytra_dict {
    param([object]$value = $null)
    if ($value -is [System.Collections.IDictionary]) {
        $copy = @{}
        foreach ($entry in $value.GetEnumerator()) {
            $copy[$entry.Key] = $entry.Value
        }
        return $copy
    }
    return @{}
}

function __pytra_error {
    param([object]$message = "")
    if ($message -eq $null) { return "" }
    if ($message -is [string]) { return $message }
    return [string]$message
}

function __pytra_bool {
    param([object]$value)
    if ($value -eq $null) { return $false }
    if ($value -is [bool]) { return $value }
    if ($value -is [int] -or $value -is [float] -or $value -is [double] -or $value -is [decimal]) { return [bool]$value }
    if ($value -is [string]) {
        if ($value.Length -eq 0) { return $false }
        return $true
    }
    if ($value -is [System.Collections.ICollection]) {
        return $value.Count -ne 0
    }
    return [bool]$value
}

function __pytra_float {
    param([object]$value)
    if ($value -eq $null) { return 0.0 }
    try {
        return [double]$value
    } catch {
        if ($value -is [bool]) { return $(if ($value) { 1.0 } else { 0.0 }) }
        return 0.0
    }
}

function __pytra_float_from_str {
    param([string]$value)
    return (__pytra_float $value)
}

function __pytra_pow {
    param([object]$base, [object]$exp)
    $left = __pytra_float $base
    $right = __pytra_float $exp
    return [Math]::Pow($left, $right)
}

function __pytra_range {
    param(
        [object]$start,
        [object]$stop = $null,
        [object]$step = 1
    )

    $from = 0
    $to = 0
    if ($stop -eq $null) {
        $to = __pytra_int $start
    } else {
        $from = __pytra_int $start
        $to = __pytra_int $stop
    }
    $step_value = __pytra_int $step
    if ($step_value -eq 0) {
        throw "[PowerShell backend experimental] range step must not be 0"
    }

    $result = New-Object System.Collections.Generic.List[int]
    if ($step_value -gt 0) {
        for ($i = $from; $i -lt $to; $i += $step_value) {
            [void]$result.Add($i)
        }
        return [int[]]$result
    }

    $current = $from
    while ($current -gt $to) {
        [void]$result.Add($current)
        $current += $step_value
    }
    return [int[]]$result
}

# stdlib native seam functions are in src/runtime/powershell/std/*_native.ps1
# They are dot-sourced by the transpiled stdlib modules (math/east.ps1 etc.)

function glob {
    param($pattern)
    $items = Get-ChildItem -Path $pattern -ErrorAction SilentlyContinue
    if ($items -eq $null) { return @() }
    return @($items | ForEach-Object { $_.FullName })
}

function __pytra_open {
    param($path, $mode = "r", $encoding = "utf-8")
    # Return a .NET stream object directly so that .write()/.read()/.close()
    # work as native .NET method calls (no hashtable wrapper needed).
    if ($mode -eq "wb" -or $mode -eq "ab") {
        $fm = if ($mode -eq "ab") { [System.IO.FileMode]::Append } else { [System.IO.FileMode]::Create }
        return [System.IO.File]::Open($path, $fm, [System.IO.FileAccess]::Write)
    }
    if ($mode -eq "w" -or $mode -eq "wt") {
        return [System.IO.StreamWriter]::new($path, $false, [System.Text.Encoding]::UTF8)
    }
    if ($mode -eq "a" -or $mode -eq "at") {
        return [System.IO.StreamWriter]::new($path, $true, [System.Text.Encoding]::UTF8)
    }
    if ($mode -eq "r" -or $mode -eq "rt") {
        return [System.IO.StreamReader]::new($path, [System.Text.Encoding]::UTF8)
    }
    if ($mode -eq "rb") {
        return [System.IO.File]::OpenRead($path)
    }
    throw "open: unsupported mode: $mode"
}

function __pytra_file_write {
    param([object]$stream, [object]$data)
    if ($stream -eq $null) { return 0 }
    if ($data -is [byte[]]) {
        $stream.Write($data, 0, $data.Length)
        return $data.Length
    }
    if ($data -is [array] -or $data -is [System.Collections.IList]) {
        # Use direct [byte[]] cast — ~10x faster than ForEach-Object pipeline
        $bytes = [byte[]]$data
        $stream.Write($bytes, 0, $bytes.Length)
        return $bytes.Length
    }
    if ($data -is [string]) {
        if ($stream -is [System.IO.StreamWriter]) {
            $stream.Write($data)
        } elseif ($stream -is [System.IO.Stream]) {
            $bytes = [System.Text.Encoding]::UTF8.GetBytes($data)
            $stream.Write($bytes, 0, $bytes.Length)
        } else {
            # Non-stream object: try .Write() method directly
            $stream.Write($data)
        }
        return $data.Length
    }
    return 0
}

function __pytra_file_read {
    param([object]$stream)
    if ($stream -eq $null) { return "" }
    if ($stream -is [System.IO.StreamReader]) {
        return $stream.ReadToEnd()
    }
    if ($stream.PSObject.Methods.Name -contains "ReadToEnd") {
        return $stream.ReadToEnd()
    }
    return ""
}

function __pytra_file_enter {
    param([object]$stream)
    return $stream
}

function __pytra_file_exit {
    param([object]$stream, [object]$exc_type = $null, [object]$exc_val = $null, [object]$exc_tb = $null)
    if ($stream -eq $null) { return $null }
    if ($stream.PSObject.Methods.Name -contains "Close") {
        $stream.Close()
        return $null
    }
    if ($stream.PSObject.Methods.Name -contains "Dispose") {
        $stream.Dispose()
    }
    return $null
}

function __pytra_in {
    param($item, $collection)
    if ($collection -is [hashtable] -or $collection -is [System.Collections.IDictionary]) {
        return $collection.Contains((__pytra_set_key $item))
    }
    if ($collection -is [string]) {
        return $collection.Contains([string]$item)
    }
    if ($collection -is [array] -or $collection -is [System.Collections.IList]) {
        return ($collection -contains $item)
    }
    if ($collection -is [System.Collections.ICollection] -or $collection -is [System.Collections.IEnumerable]) {
        return (@($collection) -contains $item)
    }
    return $false
}

function __pytra_not_in {
    param($item, $collection)
    return -not (__pytra_in $item $collection)
}

function __pytra_list_index {
    param([object]$list, [object]$item)
    if ($item -is [char]) { $item = [string]$item }
    if ($list -is [System.Collections.IList]) { return $list.IndexOf($item) }
    return [array]::IndexOf($list, $item)
}

function __pytra_list_pop {
    param([object]$list, [object]$idx = -1)
    if ($list -eq $null) { return $null }
    # Handle deque objects
    if ($list -is [hashtable] -and $list.ContainsKey("__type__") -and $list["__type__"] -eq "deque") {
        $data = $list["__data__"]
        if ($data.Count -eq 0) { throw "pop from empty deque" }
        $val = $data.Last.Value
        $data.RemoveLast()
        return ,$val
    }
    $cnt = if ($list -is [System.Collections.IList]) { $list.Count } else { $list.Length }
    if ($cnt -eq 0) { throw "pop from empty list" }
    $i = [int]$idx
    if ($i -lt 0) { $i = $cnt + $i }
    if ($i -lt 0 -or $i -ge $cnt) { throw "pop index out of range" }
    $val = $list[$i]
    $list.RemoveAt($i)
    return ,$val
}

function __pytra_list_idx {
    param([object]$list, [object]$idx)
    $i = [int]$idx
    if ($list -is [System.Collections.IList]) {
        if ($i -lt 0) { $i = $list.Count + $i }
        return $list[$i]
    }
    if ($i -lt 0) { $i = $list.Length + $i }
    return $list[$i]
}

function __pytra_seq_len {
    param([object]$s)
    if ($s -is [System.Collections.IList]) { return $s.Count }
    return $s.Length
}

function __pytra_str_slice {
    param($s, $start, $stop)
    if ($s -eq $null) { return "" }
    if ($s -is [System.Collections.IList]) {
        $len = $s.Count
        if ($start -lt 0) { $start = [Math]::Max(0, $len + $start) }
        if ($stop -lt 0) { $stop = [Math]::Max(0, $len + $stop) }
        if ($stop -gt $len) { $stop = $len }
        if ($start -ge $stop) { return [System.Collections.Generic.List[object]]::new() }
        $result = [System.Collections.Generic.List[object]]::new()
        for ($__i = $start; $__i -lt $stop; $__i++) { [void]$result.Add($s[$__i]) }
        return ,$result
    }
    if ($s -is [array]) {
        $len = $s.Length
        if ($start -lt 0) { $start = [Math]::Max(0, $len + $start) }
        if ($stop -lt 0) { $stop = [Math]::Max(0, $len + $stop) }
        if ($stop -gt $len) { $stop = $len }
        if ($start -ge $stop) { return @() }
        return ,@($s[$start..($stop - 1)])
    }
    $len = $s.Length
    if ($start -lt 0) { $start = [Math]::Max(0, $len + $start) }
    if ($stop -lt 0) { $stop = [Math]::Max(0, $len + $stop) }
    if ($stop -gt $len) { $stop = $len }
    if ($start -ge $stop) { return "" }
    return $s.Substring($start, $stop - $start)
}

function __pytra_reversed {
    param([object]$value)
    if ($value -eq $null) { return ,@() }
    if ($value -is [string]) {
        $chars = $value.ToCharArray()
        [array]::Reverse($chars)
        return -join $chars
    }
    $copy = @($value)
    [array]::Reverse($copy)
    return ,$copy
}

function __pytra_zip {
    param([object]$a, [object]$b)
    if ($a -eq $null -or $b -eq $null) { return @() }
    $aArr = if ($a -is [System.Collections.IList]) { $a.ToArray() } else { @($a) }
    $bArr = if ($b -is [System.Collections.IList]) { $b.ToArray() } else { @($b) }
    $result = @()
    $len = [Math]::Min($aArr.Count, $bArr.Count)
    for ($i = 0; $i -lt $len; $i++) {
        $result += ,@($aArr[$i], $bArr[$i])
    }
    return $result
}

function __pytra_map {
    param([object]$fn, [object]$items)
    if ($items -eq $null) { return @() }
    $result = @()
    foreach ($item in $items) {
        $result += ,@(& $fn $item)
    }
    return $result
}

function __pytra_filter {
    param([object]$fn, [object]$items)
    if ($items -eq $null) { return @() }
    $result = @()
    foreach ($item in $items) {
        if (& $fn $item) {
            $result += ,@($item)
        }
    }
    return $result
}

function __pytra_sum {
    param([object]$items, [object]$start = 0)
    if ($items -eq $null) { return $start }
    $acc = $start
    foreach ($item in $items) { $acc = $acc + $item }
    return $acc
}

function __pytra_max {
    param([object]$a, [object]$b)
    if ($a -ge $b) { return $a } else { return $b }
}

function __pytra_min {
    param([object]$a, [object]$b)
    if ($a -le $b) { return $a } else { return $b }
}

function __pytra_abs {
    param([object]$a)
    if ($a -lt 0) { return -$a } else { return $a }
}

function __pytra_list_remove {
    param([object]$list, [object]$value)
    $idx = [array]::IndexOf($list, $value)
    if ($idx -ge 0) {
        $result = @()
        for ($i = 0; $i -lt $list.Length; $i++) {
            if ($i -ne $idx) { $result += ,@($list[$i]) }
        }
        return $result
    }
    return $list
}

function __pytra_getattr {
    param([object]$obj, [string]$attr)
    if ($obj -is [hashtable] -or $obj -is [System.Collections.IDictionary]) {
        # Direct key access first
        if ($obj.Contains($attr)) { return $obj[$attr] }
        # Try property getter: ClassName_attr($obj) (class instances only)
        if ($obj -is [hashtable] -and $obj.ContainsKey("__type__")) {
            $getter = $obj["__type__"] + "_" + $attr
            if (Get-Command $getter -ErrorAction SilentlyContinue) {
                return (& (Get-Command $getter) $obj)
            }
        }
    }
    return $null
}

function __pytra_type_check {
    param([object]$obj, [string]$type_name)
    if ($obj -eq $null) { return $false }
    # Primitive type checks
    if ($type_name -eq "int" -or $type_name -eq "int64") { return ($obj -is [int] -or $obj -is [long]) }
    if ($type_name -eq "float" -or $type_name -eq "float64") { return ($obj -is [double] -or $obj -is [float]) }
    if ($type_name -eq "str") { return ($obj -is [string]) }
    if ($type_name -eq "bool") { return ($obj -is [bool]) }
    if ($type_name -eq "list") { return ($obj -is [array] -or $obj -is [System.Collections.IList]) }
    if ($type_name -eq "dict") { return ($obj -is [hashtable] -or $obj -is [System.Collections.IDictionary]) }
    # Hashtable-based class: walk __type__ and __bases__
    if ($obj -is [hashtable] -and $obj.ContainsKey("__type__")) {
        $current = $obj["__type__"]
        # Check if constructor function exists and has the right name
        while ($current -ne $null -and $current -ne "") {
            if ($current -eq $type_name) { return $true }
            # Look up base class via ClassName constructor's __bases__ convention
            # The emitter stores base info in a global $__pytra_bases hashtable
            $base = $null
            if (Test-Path variable:__pytra_bases) {
                $base = $__pytra_bases[$current]
            }
            if ($base -eq $null -or $base -eq "") { break }
            $bases = @($base)
            foreach ($candidate in $bases) {
                if ($candidate -eq $type_name) { return $true }
                if ($candidate -ne $current -and (__pytra_type_check @{"__type__" = $candidate} $type_name)) { return $true }
            }
            break
        }
    }
    return $false
}

function __pytra_exc_is {
    param([string]$thrown_type, [string]$handler_type)
    if ($thrown_type -eq "" -or $handler_type -eq "") { return $true }
    $current = $thrown_type
    while ($current -ne $null -and $current -ne "") {
        if ($current -eq $handler_type) { return $true }
        $base = $null
        if (Test-Path variable:__pytra_bases) { $base = $__pytra_bases[$current] }
        if ($null -eq $base -or $base -eq "" -or $base -eq $current) { break }
        $current = $base
    }
    return $false
}

function PytraNotImplemented {
    param([string]$Feature = "")
    if ($Feature -ne "") {
        throw "[PowerShell backend experimental] Not implemented: $Feature"
    }
    throw "[PowerShell backend experimental] Not implemented feature"
}

function py_assert_eq {
    param($a, $b, $msg)
    $sa = (__pytra_str $a)
    $sb = (__pytra_str $b)
    if ($sa -ne $sb) {
        $label = $(if ($msg) { " ($msg)" } else { "" })
        throw "assertion failed: $sa != $sb$label"
    }
    return $true
}

function py_assert_true {
    param($value, $msg)
    if (-not $value) {
        $label = $(if ($msg) { " ($msg)" } else { "" })
        throw "assertion failed: expected true$label"
    }
    return $true
}

function py_assert_all {
    param([object[]]$checks)
    foreach ($c in $checks) {
        if (-not $c) {
            throw "assertion failed in py_assert_all"
        }
    }
    return $true
}

function py_assert_stdout {
    param($expected, $fn)
    # Capture [Console]::Out.WriteLine output by redirecting Console.Out
    $captured = @()
    $old_out = [Console]::Out
    $sw = [System.IO.StringWriter]::new()
    [Console]::SetOut($sw)
    try {
        if ($fn -is [scriptblock]) {
            & $fn | Out-Null
        } elseif ($fn -is [string]) {
            & (Get-Command $fn) | Out-Null
        } else {
            [Console]::SetOut($old_out)
            return $true
        }
    } finally {
        [Console]::SetOut($old_out)
    }
    $raw = $sw.ToString()
    if ($raw -ne "") {
        $captured = @($raw.TrimEnd("`r`n").Split("`n") | ForEach-Object { $_.TrimEnd("`r") })
    }
    if ($expected -eq $null) { return $true }
    $exp_arr = @($expected)
    if ($captured.Length -ne $exp_arr.Length) {
        throw "py_assert_stdout: expected $($exp_arr.Length) lines, got $($captured.Length): [$($captured -join ', ')]"
    }
    for ($i = 0; $i -lt $exp_arr.Length; $i++) {
        if ([string]$captured[$i] -ne [string]$exp_arr[$i]) {
            throw "py_assert_stdout: line $i mismatch: expected '$($exp_arr[$i])' got '$($captured[$i])'"
        }
    }
    return $true
}

function __pytra_list_sort {
    param([object]$list)
    if ($list -eq $null) { return }
    $arr = @($list)
    [array]::Sort($arr)
    $list.Clear()
    foreach ($item in $arr) { [void]$list.Add($item) }
}

function __pytra_sorted {
    param([object]$value)
    if ($value -is [System.Collections.IDictionary]) {
        $arr = @($value.Keys)
    } else {
        $arr = @($value)
    }
    [array]::Sort($arr)
    return ,(__pytra_mklist @arr)
}

function __pytra_list_reverse {
    param([object]$list)
    if ($list -eq $null) { return }
    $arr = @($list)
    [array]::Reverse($arr)
    $list.Clear()
    foreach ($item in $arr) { [void]$list.Add($item) }
}

function __pytra_dict_pop {
    param([object]$dict, [object]$key, [object]$default = $null)
    if ($dict -eq $null) { return $default }
    if ($dict.Contains($key)) {
        $val = $dict[$key]
        $dict.Remove($key)
        return $val
    }
    return $default
}

function __pytra_dict_setdefault {
    param([object]$dict, [object]$key, [object]$default = $null)
    if ($dict -eq $null) { return $default }
    if (-not $dict.Contains($key)) {
        $dict[$key] = $default
    }
    return $dict[$key]
}

function __pytra_list_clear {
    param([object]$list)
    if ($list -eq $null) { return }
    $list.Clear()
}

function __pytra_str_strip {
    param([object]$s) return [string]$s.Trim()
}

function __pytra_str_rstrip {
    param([object]$s) return [string]$s.TrimEnd()
}

function __pytra_str_lstrip {
    param([object]$s) return [string]$s.TrimStart()
}

function __pytra_str_startswith {
    param([object]$s, [object]$prefix) return ([string]$s).StartsWith([string]$prefix)
}

function __pytra_str_endswith {
    param([object]$s, [object]$suffix) return ([string]$s).EndsWith([string]$suffix)
}

function __pytra_str_replace {
    param([object]$s, [object]$old, [object]$new_) return ([string]$s).Replace([string]$old, [string]$new_)
}

function __pytra_str_find {
    param([object]$s, [object]$sub) return [string]$s.IndexOf([string]$sub)
}

function __pytra_str_rfind {
    param([object]$s, [object]$sub) return [string]$s.LastIndexOf([string]$sub)
}

function __pytra_str_index {
    param([object]$s, [object]$sub)
    $idx = [string]$s.IndexOf([string]$sub)
    if ($idx -lt 0) { throw "substring not found" }
    return $idx
}

function __pytra_str_count {
    param([object]$s, [object]$sub)
    $str = [string]$s; $substr = [string]$sub
    if ($substr.Length -eq 0) { return $str.Length + 1 }
    $count = 0; $pos = 0
    while ($true) { $idx = $str.IndexOf($substr, $pos); if ($idx -lt 0) { break }; $count++; $pos = $idx + $substr.Length }
    return $count
}

function __pytra_str_split {
    param([object]$s, [object]$sep = $null)
    if ($sep -eq $null) { return [System.Collections.Generic.List[object]]($s.Split([char[]]@(' ',"`t","`n","`r"), [System.StringSplitOptions]::RemoveEmptyEntries)) }
    $parts = ([string]$s).Split([string]$sep)
    $result = [System.Collections.Generic.List[object]]::new()
    foreach ($p in $parts) { [void]$result.Add($p) }
    return ,$result
}

function __pytra_str_join {
    param([object]$sep, [object]$iterable)
    $arr = @($iterable)
    return [string]::Join([string]$sep, $arr)
}

function __pytra_str_format {
    param([object]$fmt, [Parameter(ValueFromRemainingArguments = $true)][object[]]$rest)
    return [string]::Format([string]$fmt, $rest)
}

function __pytra_str_upper {
    param([object]$s) return ([string]$s).ToUpper()
}

function __pytra_str_lower {
    param([object]$s) return ([string]$s).ToLower()
}

function __pytra_str_isdigit {
    param([object]$s)
    $str = [string]$s
    if ($str.Length -eq 0) { return $false }
    if ($str.Length -eq 1) { return [char]::IsDigit($str[0]) }
    foreach ($c in $str.ToCharArray()) { if (-not [char]::IsDigit($c)) { return $false } }
    return $true
}

function __pytra_str_isalnum {
    param([object]$s)
    $str = [string]$s
    if ($str.Length -eq 0) { return $false }
    if ($str.Length -eq 1) { return [char]::IsLetterOrDigit($str[0]) }
    foreach ($c in $str.ToCharArray()) { if (-not [char]::IsLetterOrDigit($c)) { return $false } }
    return $true
}

function __pytra_str_isalpha {
    param([object]$s)
    $str = [string]$s
    if ($str.Length -eq 0) { return $false }
    if ($str.Length -eq 1) { return [char]::IsLetter($str[0]) }
    foreach ($c in $str.ToCharArray()) { if (-not [char]::IsLetter($c)) { return $false } }
    return $true
}

function __pytra_str_isspace {
    param([object]$s)
    $str = [string]$s
    if ($str.Length -eq 0) { return $false }
    if ($str.Length -eq 1) { return [char]::IsWhiteSpace($str[0]) }
    foreach ($c in $str.ToCharArray()) { if (-not [char]::IsWhiteSpace($c)) { return $false } }
    return $true
}

function __pytra_str_isupper {
    param([object]$s)
    $str = [string]$s
    if ($str.Length -eq 0) { return $false }
    $hasLetter = $false
    foreach ($c in $str.ToCharArray()) {
        if ([char]::IsLetter($c)) {
            $hasLetter = $true
            if ([char]::IsLower($c)) { return $false }
        }
    }
    return $hasLetter
}

function __pytra_str_islower {
    param([object]$s)
    $str = [string]$s
    if ($str.Length -eq 0) { return $false }
    $hasLetter = $false
    foreach ($c in $str.ToCharArray()) {
        if ([char]::IsLetter($c)) {
            $hasLetter = $true
            if ([char]::IsUpper($c)) { return $false }
        }
    }
    return $hasLetter
}

function __pytra_int_from_str {
    param([object]$s) return [int64]$s
}

function __pytra_list_extend {
    param([object]$list, [object]$items)
    if ($items -eq $null) { return }
    foreach ($item in $items) { [void]$list.Add($item) }
}

function __pytra_list_insert {
    param([object]$list, [object]$index, [object]$value)
    if ($list -eq $null) { return $null }
    $list.Insert([int]$index, $value)
    return $list
}

function __pytra_list_copy {
    param([object]$list)
    return ,@($list)
}

# (duplicate removed - see __pytra_list_index above)

function __pytra_dict_clear {
    param([object]$dict)
    if ($dict -eq $null) { return }
    $dict.Clear()
}

function __pytra_dict_update {
    param([object]$dict, [object]$other)
    if ($dict -eq $null -or $other -eq $null) { return $dict }
    foreach ($k in $other.Keys) { $dict[$k] = $other[$k] }
    return $dict
}

function __pytra_set_clear {
    param([object]$set_)
    if ($set_ -eq $null) { return }
    $set_.Clear()
}

function __pytra_set_discard {
    param([object]$set_, [object]$value)
    if ($set_ -eq $null) { return }
    [void]$set_.Remove((__pytra_set_key $value))
}

function __pytra_set_remove {
    param([object]$set_, [object]$value)
    if ($set_ -eq $null) { return }
    $k = (__pytra_set_key $value)
    if (-not $set_.ContainsKey($k)) { throw "KeyError: $value" }
    [void]$set_.Remove($k)
}

function __pytra_set_update {
    param([object]$set_, [object]$values)
    if ($set_ -eq $null -or $values -eq $null) { return $set_ }
    if ($values -is [System.Collections.IDictionary]) {
        foreach ($k in $values.Keys) {
            $set_[(__pytra_set_key $k)] = $true
        }
        return $set_
    }
    foreach ($item in $values) {
        $set_[(__pytra_set_key $item)] = $true
    }
    return $set_
}

# ---------------------------------------------------------------------------
# py_format_value — Python format spec mini-language implementation
# ---------------------------------------------------------------------------

function __pytra_fv_insert_grouping {
    param([string]$digits, [string]$sep, [int]$sz)
    $n = $digits.Length
    if ($n -le $sz) { return $digits }
    $result = ""
    $pos = $n
    while ($pos -gt 0) {
        $start = [Math]::Max(0, $pos - $sz)
        $chunk = $digits.Substring($start, $pos - $start)
        if ($result -ne "") { $result = $chunk + $sep + $result }
        else { $result = $chunk }
        $pos = $start
    }
    return $result
}

function py_format_value {
    param([object]$value, [string]$spec)
    $ic = [System.Globalization.CultureInfo]::InvariantCulture
    if ($spec -eq "") { return (__pytra_str $value) }

    # Parse spec: [[fill]align][sign][z][#][0][width][grouping][.precision][type]
    $fill = ""; $align = ""; $sign = ""; $width = ""; $grouping = ""; $precision = ""; $typec = ""
    $pos = 0; $n = $spec.Length
    if ($n -ge 2 -and ($spec[1] -eq '<' -or $spec[1] -eq '>' -or $spec[1] -eq '^' -or $spec[1] -eq '=')) {
        $fill = [string]$spec[0]; $align = [string]$spec[1]; $pos = 2
    } elseif ($n -ge 1 -and ($spec[0] -eq '<' -or $spec[0] -eq '>' -or $spec[0] -eq '^' -or $spec[0] -eq '=')) {
        $align = [string]$spec[0]; $pos = 1
    }
    if ($pos -lt $n -and ($spec[$pos] -eq '+' -or $spec[$pos] -eq '-' -or $spec[$pos] -eq ' ')) {
        $sign = [string]$spec[$pos]; $pos++
    }
    if ($pos -lt $n -and $spec[$pos] -eq 'z') { $pos++ }
    if ($pos -lt $n -and $spec[$pos] -eq '#') { $pos++ }
    if ($pos -lt $n -and $spec[$pos] -eq '0') {
        if ($fill -eq "" -and $align -eq "") { $fill = "0"; $align = "=" }
        $pos++
    }
    $ws = $pos
    while ($pos -lt $n -and $spec[$pos] -ge '0' -and $spec[$pos] -le '9') { $pos++ }
    if ($pos -gt $ws) { $width = $spec.Substring($ws, $pos - $ws) }
    if ($pos -lt $n -and ($spec[$pos] -eq ',' -or $spec[$pos] -eq '_')) { $grouping = [string]$spec[$pos]; $pos++ }
    if ($pos -lt $n -and $spec[$pos] -eq '.') {
        $pos++; $ps2 = $pos
        while ($pos -lt $n -and $spec[$pos] -ge '0' -and $spec[$pos] -le '9') { $pos++ }
        $precision = $spec.Substring($ps2, $pos - $ps2)
    }
    if ($pos -lt $n) { $typec = [string]$spec[$pos] }

    # Format core
    $raw = ""
    $is_str_type = $typec -eq "s" -or ($typec -eq "" -and $value -is [string])

    if ($is_str_type) {
        $raw = (__pytra_str $value)
        if ($precision -ne "") { $plen = [int]$precision; if ($raw.Length -gt $plen) { $raw = $raw.Substring(0, $plen) } }
    } elseif ($value -is [bool]) {
        $raw = if ($value) { "True" } else { "False" }
    } elseif ($value -is [int] -or $value -is [long]) {
        $ival = [long]$value
        $is_neg = $ival -lt 0
        $absv = if ($is_neg) { -$ival } else { $ival }
        if ($typec -eq "x") { $raw = [Convert]::ToString($absv, 16) }
        elseif ($typec -eq "X") { $raw = ([Convert]::ToString($absv, 16)).ToUpper() }
        elseif ($typec -eq "o") { $raw = [Convert]::ToString($absv, 8) }
        elseif ($typec -eq "b") { $raw = [Convert]::ToString($absv, 2) }
        elseif ($typec -eq "f" -or $typec -eq "F" -or $typec -eq "e" -or $typec -eq "E" -or $typec -eq "g" -or $typec -eq "G" -or $typec -eq "%") {
            # Delegate int with float-type spec to float path
            return py_format_value ([double]$value) $spec
        }
        else { $raw = [string]$absv }
        if ($grouping -eq ",") { $raw = (__pytra_fv_insert_grouping $raw "," 3) }
        elseif ($grouping -eq "_") {
            $gsz = if ($typec -eq "x" -or $typec -eq "X" -or $typec -eq "b" -or $typec -eq "o") { 4 } else { 3 }
            $raw = (__pytra_fv_insert_grouping $raw "_" $gsz)
        }
        if ($is_neg) { $raw = "-" + $raw }
        elseif ($sign -eq "+") { $raw = "+" + $raw }
        elseif ($sign -eq " ") { $raw = " " + $raw }
    } elseif ($value -is [double] -or $value -is [float]) {
        $dval = [double]$value
        $is_neg = $dval -lt 0
        $absv = if ($is_neg) { -$dval } else { $dval }
        $prec = if ($precision -ne "") { [int]$precision } else { 6 }
        if ($typec -eq "f" -or $typec -eq "F" -or $typec -eq "") {
            $raw = $absv.ToString("F$prec", $ic)
        } elseif ($typec -eq "e") {
            $raw = $absv.ToString("e$prec", $ic)
            # Python uses e+XX not e+0XX, normalize
            $raw = [System.Text.RegularExpressions.Regex]::Replace($raw, 'e([+-])0+(\d{2,})', 'e$1$2')
            $raw = [System.Text.RegularExpressions.Regex]::Replace($raw, 'e([+-])(\d)$', 'e${1}0$2')
        } elseif ($typec -eq "E") {
            $raw = $absv.ToString("E$prec", $ic)
            $raw = [System.Text.RegularExpressions.Regex]::Replace($raw, 'E([+-])0+(\d{2,})', 'E$1$2')
            $raw = [System.Text.RegularExpressions.Regex]::Replace($raw, 'E([+-])(\d)$', 'E${1}0$2')
        } elseif ($typec -eq "g" -or $typec -eq "G") {
            $gprec = if ($prec -eq 0) { 1 } else { $prec }
            $raw = $absv.ToString("G$gprec", $ic)
            if ($typec -eq "g") { $raw = $raw.ToLower() }
        } elseif ($typec -eq "%") {
            $raw = ($absv * 100.0).ToString("F$prec", $ic) + "%"
        } else {
            $raw = $absv.ToString("F$prec", $ic)
        }
        if ($grouping -ne "") {
            $dot_pos = $raw.IndexOf('.')
            $pct_pos = $raw.IndexOf('%')
            if ($dot_pos -ge 0) {
                $ip = $raw.Substring(0, $dot_pos)
                $fp = $raw.Substring($dot_pos)
                $raw = (__pytra_fv_insert_grouping $ip $grouping 3) + $fp
            } elseif ($pct_pos -ge 0) {
                $raw = (__pytra_fv_insert_grouping $raw.Substring(0, $pct_pos) $grouping 3) + "%"
            } else {
                $raw = (__pytra_fv_insert_grouping $raw $grouping 3)
            }
        }
        if ($is_neg) { $raw = "-" + $raw }
        elseif ($sign -eq "+") { $raw = "+" + $raw }
        elseif ($sign -eq " ") { $raw = " " + $raw }
    } else {
        $raw = (__pytra_str $value)
    }

    # Apply width / alignment
    if ($width -eq "") { return $raw }
    $w = [int]$width
    if ($raw.Length -ge $w) { return $raw }
    if ($fill -eq "") { $fill = " " }
    $pad = $w - $raw.Length
    $padding = $fill * $pad
    if ($align -eq "<") { return $raw + $padding }
    if ($align -eq "^") { $lp = [int]($pad / 2); $rp = $pad - $lp; return ($fill * $lp) + $raw + ($fill * $rp) }
    if ($align -eq "=") {
        if ($raw.Length -gt 0 -and ($raw[0] -eq '-' -or $raw[0] -eq '+' -or $raw[0] -eq ' ')) {
            return [string]$raw[0] + $padding + $raw.Substring(1)
        }
        return $padding + $raw
    }
    # Default: right-align for numbers, left-align for strings
    if ($is_str_type) { return $raw + $padding }
    return $padding + $raw
}
