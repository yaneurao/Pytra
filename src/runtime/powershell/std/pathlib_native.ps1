# pathlib_native.ps1 — native seam for pathlib.Path / pytra.std.pathlib.Path

function Path {
    param($self, $path_str)
    if ($null -eq $self) { $self = @{} }
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
        Path $parentObj $parentStr
        $self["parent"] = $parentObj
    }
}

function Path___str__ {
    param($self)
    return $self["_p"]
}

function Path_joinpath {
    param($self, $other)
    if ($other -is [hashtable] -and $other["__type__"] -eq "Path") {
        $joined = [System.IO.Path]::Combine($self["_p"], $other["_p"])
    } else {
        $joined = [System.IO.Path]::Combine($self["_p"], [string]$other)
    }
    $result = @{}
    Path $result $joined
    return $result
}

function Path_exists {
    param($self)
    return (Test-Path $self["_p"])
}

function Path_cwd {
    $result = @{}
    Path $result ([System.Environment]::CurrentDirectory)
    return $result
}

function Path_mkdir {
    param($self, $parents = $false, $exist_ok = $false)
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
    $utf8_no_bom = [System.Text.UTF8Encoding]::new($false)
    [System.IO.File]::WriteAllText($self["_p"], $text, $utf8_no_bom)
}

function Path_read_text {
    param($self, $encoding = "utf-8")
    return [System.IO.File]::ReadAllText($self["_p"], [System.Text.Encoding]::UTF8)
}

function Path_is_file {
    param($self)
    return (Test-Path $self["_p"] -PathType Leaf)
}

function Path_is_dir {
    param($self)
    return (Test-Path $self["_p"] -PathType Container)
}

function Path___div__ {
    param($self, $other)
    return (Path_joinpath $self $other)
}
