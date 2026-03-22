Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function __pytra_print {
    param(
        [Parameter(ValueFromRemainingArguments = $true)]
        [object[]] $items
    )

    if ($items.Count -eq 0) {
        [Console]::Out.WriteLine("")
        return
    }

    $parts = New-Object System.Collections.Generic.List[string]
    foreach ($item in $items) {
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

function __pytra_str {
    param([object]$value)
    if ($value -eq $null) { return "None" }
    if ($value -is [bool]) { return $(if ($value) { "True" } else { "False" }) }
    # Hashtable-based class with __str__ method
    if ($value -is [hashtable] -and $value.ContainsKey("__type__")) {
        $tn = $value["__type__"]
        $str_fn = $tn + "___str__"
        if (Get-Command $str_fn -ErrorAction SilentlyContinue) {
            return [string](& (Get-Command $str_fn) $value)
        }
    }
    if ($value -is [hashtable]) { return "hashtable" }
    return [string]$value
}

function __pytra_int {
    param([object]$value)
    if ($value -eq $null) { return 0 }
    try {
        return [int]$value
    } catch {
        if ($value -is [bool]) { return $(if ($value) { 1 } else { 0 }) }
        return 0
    }
}

function __pytra_bytearray {
    param([object]$size = 0)
    # 配列が渡された場合はコピーして返す
    if ($size -is [array] -or $size -is [System.Collections.IList]) {
        $result = New-Object System.Collections.Generic.List[int]
        foreach ($item in $size) {
            [void]$result.Add((__pytra_int $item))
        }
        return ,[int[]]$result.ToArray()
    }
    $count = __pytra_int $size
    if ($count -lt 0) {
        throw "[PowerShell backend experimental] negative bytearray size"
    }
    $result = New-Object System.Collections.Generic.List[int]
    for ($i = 0; $i -lt $count; $i++) {
        [void]$result.Add(0)
    }
    return ,[int[]]$result.ToArray()
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
    if ($value -is [System.Collections.ICollection]) {
        $result = New-Object System.Collections.Generic.List[object]
        foreach ($item in $value) {
            [void]$result.Add((__pytra_int $item))
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

function __pytra_set {
    param([object[]]$values)
    $result = @{}
    foreach ($item in $values) {
        $result["$item"] = $true
    }
    return $result
}

function __pytra_dict {
    param([object]$value = $null)
    if ($value -is [hashtable]) {
        $copy = @{}
        foreach ($key in $value.Keys) {
            $copy[$key] = $value[$key]
        }
        return $copy
    }
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

function open {
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
    if ($data -is [array] -or $data -is [System.Collections.IList]) {
        $bytes = [byte[]]@($data | ForEach-Object { [byte]$_ })
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

function __pytra_in {
    param($item, $collection)
    if ($collection -is [hashtable] -or $collection -is [System.Collections.IDictionary]) {
        return $collection.ContainsKey($item)
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

function __pytra_list_pop {
    param([object]$list)
    if ($list -eq $null -or $list.Length -eq 0) { return $null }
    return $list[-1]
}

function __pytra_str_slice {
    param($s, $start, $stop)
    if ($s -eq $null) { return "" }
    if ($s -is [array] -or $s -is [System.Collections.IList]) {
        $len = $s.Length
        if ($start -lt 0) { $start = [Math]::Max(0, $len + $start) }
        if ($stop -lt 0) { $stop = [Math]::Max(0, $len + $stop) }
        if ($stop -gt $len) { $stop = $len }
        if ($start -ge $stop) { return @() }
        return @($s[$start..($stop - 1)])
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
    if ($value -eq $null) { return @() }
    if ($value -is [string]) {
        $chars = $value.ToCharArray()
        [array]::Reverse($chars)
        return -join $chars
    }
    $copy = @($value)
    [array]::Reverse($copy)
    return $copy
}

function __pytra_zip {
    param([object]$a, [object]$b)
    if ($a -eq $null -or $b -eq $null) { return @() }
    $result = @()
    $len = [Math]::Min($a.Length, $b.Length)
    for ($i = 0; $i -lt $len; $i++) {
        $result += ,@($a[$i], $b[$i])
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
    if ($obj -is [hashtable]) {
        # Direct key access first
        if ($obj.ContainsKey($attr)) { return $obj[$attr] }
        # Try property getter: ClassName_attr($obj)
        if ($obj.ContainsKey("__type__")) {
            $getter = $obj["__type__"] + "_" + $attr
            if (Get-Command $getter -ErrorAction SilentlyContinue) {
                return (& (Get-Command $getter) $obj)
            }
        }
    }
    return $null
}

function __pytra_isinstance {
    param([object]$obj, [string]$type_name)
    if ($obj -eq $null) { return $false }
    # Normalize PYTRA_TID_* names to primitive names
    if ($type_name -eq "PYTRA_TID_BOOL") { $type_name = "bool" }
    elseif ($type_name -eq "PYTRA_TID_INT") { $type_name = "int" }
    elseif ($type_name -eq "PYTRA_TID_FLOAT") { $type_name = "float" }
    elseif ($type_name -eq "PYTRA_TID_STR") { $type_name = "str" }
    elseif ($type_name -eq "PYTRA_TID_LIST") { $type_name = "list" }
    elseif ($type_name -eq "PYTRA_TID_DICT") { $type_name = "dict" }
    elseif ($type_name -eq "PYTRA_TID_NONE") { return ($obj -eq $null) }
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
            if ($base -eq $null -or $base -eq "" -or $base -eq $current) { break }
            $current = $base
        }
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
