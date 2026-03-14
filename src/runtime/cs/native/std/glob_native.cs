using System;
using System.Collections.Generic;
using System.IO;

namespace Pytra.CsModule
{
    // Generated std/glob.cs delegates host bindings through this native seam.
    public static class glob_native
    {
        public static List<string> glob(string pattern)
        {
            try
            {
                int slashPos = pattern.LastIndexOf('/');
                int backslashPos = pattern.LastIndexOf('\\');
                int separatorPos = Math.Max(slashPos, backslashPos);
                string directoryPart = separatorPos < 0 ? "." : pattern.Substring(0, separatorPos);
                string mask = separatorPos < 0 ? pattern : pattern.Substring(separatorPos + 1);
                bool hasWildcard = mask.Contains("*") || mask.Contains("?");
                bool rooted = Path.IsPathRooted(directoryPart);
                string directoryForSearch = string.IsNullOrEmpty(directoryPart) ? "." : directoryPart;
                string directoryForOutput =
                    string.IsNullOrEmpty(directoryPart)
                    || directoryPart == "."
                        ? "."
                        : directoryPart.Replace("\\", "/");

                if (!hasWildcard)
                {
                    if (File.Exists(pattern) || Directory.Exists(pattern))
                    {
                        return new List<string> { pattern };
                    }
                    return new List<string>();
                }

                var entries = new List<string>();
                foreach (string path in Directory.GetFiles(directoryForSearch, mask, SearchOption.TopDirectoryOnly))
                {
                    if (directoryForOutput == ".")
                    {
                        entries.Add(Path.GetFileName(path));
                    }
                    else if (rooted)
                    {
                        entries.Add(Path.GetFullPath(path).Replace("\\", "/"));
                    }
                    else
                    {
                        entries.Add(directoryForOutput + "/" + Path.GetFileName(path));
                    }
                }

                foreach (string path in Directory.GetDirectories(directoryForSearch, mask, SearchOption.TopDirectoryOnly))
                {
                    if (directoryForOutput == ".")
                    {
                        entries.Add(Path.GetFileName(path));
                    }
                    else if (rooted)
                    {
                        entries.Add(Path.GetFullPath(path).Replace("\\", "/"));
                    }
                    else
                    {
                        entries.Add(directoryForOutput + "/" + Path.GetFileName(path));
                    }
                }

                return entries;
            }
            catch
            {
                return new List<string>();
            }
        }
    }
}
