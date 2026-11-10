#!/usr/bin/env python3
"""Normalize tar archive modes for reproducible packages across platforms.

Windows checkouts cannot represent Unix executable bits, so the packaging step
rewrites the archive with explicit modes and root ownership.

Usage: normalize-tar.py <archive> <executable-prefix> [...]
"""
import os
import sys
import tarfile
import tempfile

path = sys.argv[1]
prefixes = tuple(prefix[2:] if prefix.startswith("./") else prefix for prefix in sys.argv[2:])


def is_executable(name):
    normalized = name[2:] if name.startswith("./") else name
    return any(normalized.startswith(prefix) for prefix in prefixes)


directory = os.path.dirname(os.path.abspath(path))
fd, temporary = tempfile.mkstemp(dir=directory, suffix=".tar")
os.close(fd)
try:
    with tarfile.open(path, "r:*") as source, tarfile.open(temporary, "w:gz", format=tarfile.PAX_FORMAT) as target:
        for member in source:
            if member.isdir():
                member.mode = 0o755
            elif member.isfile():
                member.mode = 0o755 if is_executable(member.name) else 0o644
            if not member.issym() and not member.islnk():
                member.uid = member.gid = 0
                member.uname = member.gname = "root"
            data = source.extractfile(member) if member.isfile() else None
            target.addfile(member, data)
    os.replace(temporary, path)
except Exception:
    os.unlink(temporary)
    raise