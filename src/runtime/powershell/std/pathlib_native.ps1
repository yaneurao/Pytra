# pathlib_native.ps1 — native seam for pathlib.Path / pytra.std.pathlib.Path

function Path {
    param($self, $path_str)
    $return_self = $false
    if ($null -eq $path_str -and $null -ne $self -and -not ($self -is [hashtable])) {
        $path_str = $self
        $self = @{}
        $return_self = $true
    }
    if ($null -eq $self) { $self = @{}; $return_self = $true }
    $self["__type__"] = "Path"
    # Accept str or Path object
    if ($path_str -is [hashtable] -and $path_str["__type__"] -eq "Path") {
        $self["_p"] = $path_str["_p"]
    } else {
        $self["_p"] = [string]$path_str
    }
    # Precompute properties
    $self["name"]   = [System.IO.Path]::GetFileName($self["_p"])
    $self["stem"]   = [System.IO.Path]::GetFileNameWithoutExtension($self["_p"])
    $self["suffix"] = [System.IO.Path]::GetExtension($self["_p"])
    $d = [System.IO.Path]::GetDirectoryName($self["_p"])
    $parentStr = "."
    if ($d -ne $null -and $d -ne "") { $parentStr = $d }
    if ($parentStr -eq $self["_p"]) {
        $self["parent"] = $self
    } else {
        $parentObj = @{}
        [void](Path $parentObj $parentStr)
        $self["parent"] = $parentObj
    }
    if ($return_self) { return ,$self }
    return
}

function Path___str__ {
    param($self)
    $self = __pytra_path_obj $self
    if (($self -is [System.Collections.IList] -or $self -is [array]) -and $self.Count -eq 1) { $self = $self[0] }
    return $self["_p"]
}

function __pytra_path_obj {
    param($value)
    if (($value -is [System.Collections.IList] -or $value -is [array]) -and $value.Count -eq 1) {
        $value = $value[0]
    }
    if ($value -is [hashtable] -and $value["__type__"] -eq "Path") {
        return ,$value
    }
    return ,(Path $value)
}

function Path_joinpath {
    param($self, $other)
    $self = __pytra_path_obj $self
    if (($self -is [System.Collections.IList] -or $self -is [array]) -and $self.Count -eq 1) { $self = $self[0] }
    if ($other -is [hashtable] -and $other["__type__"] -eq "Path") {
        $joined = [System.IO.Path]::Combine($self["_p"], $other["_p"])
    } else {
        $joined = [System.IO.Path]::Combine($self["_p"], [string]$other)
    }
    $result = @{}
    [void](Path $result $joined)
    return ,$result
}

function Path_cwd {
    $result = @{}
    [void](Path $result (Get-Location).Path)
    return ,$result
}

function cwd {
    return (Path_cwd)
}

function Path_exists {
    param($self)
    $self = __pytra_path_obj $self
    if (($self -is [System.Collections.IList] -or $self -is [array]) -and $self.Count -eq 1) { $self = $self[0] }
    return (Test-Path $self["_p"])
}

function Path_mkdir {
    param($self, $parents = $false, $exist_ok = $false)
    $self = __pytra_path_obj $self
    if (($self -is [System.Collections.IList] -or $self -is [array]) -and $self.Count -eq 1) { $self = $self[0] }
    if (Test-Path $self["_p"]) {
        if (-not $exist_ok) { throw "Directory already exists: $($self["_p"])" }
        return
    }
    if ($parents) {
        New-Item -ItemType Directory -Path $self["_p"] -Force | Out-Null
    } else {
        New-Item -ItemType Directory -Path $self["_p"] | Out-Null
    }
}

function Path_write_text {
    param($self, $text, $encoding = "utf-8")
    $self = __pytra_path_obj $self
    if (($self -is [System.Collections.IList] -or $self -is [array]) -and $self.Count -eq 1) { $self = $self[0] }
    $utf8NoBom = [System.Text.UTF8Encoding]::new($false)
    [System.IO.File]::WriteAllText($self["_p"], $text, $utf8NoBom)
}

function Path_read_text {
    param($self, $encoding = "utf-8")
    $self = __pytra_path_obj $self
    if (($self -is [System.Collections.IList] -or $self -is [array]) -and $self.Count -eq 1) { $self = $self[0] }
    return [System.IO.File]::ReadAllText($self["_p"], [System.Text.Encoding]::UTF8)
}

function Path_is_file {
    param($self)
    $self = __pytra_path_obj $self
    if (($self -is [System.Collections.IList] -or $self -is [array]) -and $self.Count -eq 1) { $self = $self[0] }
    return (Test-Path $self["_p"] -PathType Leaf)
}

function Path_is_dir {
    param($self)
    $self = __pytra_path_obj $self
    if (($self -is [System.Collections.IList] -or $self -is [array]) -and $self.Count -eq 1) { $self = $self[0] }
    return (Test-Path $self["_p"] -PathType Container)
}

function Path___div__ {
    param($self, $other)
    return (Path_joinpath $self $other)
}
