"""Append text scenes (.tscn) to the .pck produced by BSchneppe.StS2.PckPacker.

PckPacker refuses to pack .tscn files (Godot normally compiles them to .scn), but
the game engine can load text scenes fine - the base game itself ships a thousand
of them.  So after the packer runs we rewrite the pack with the extra scenes.

PCK format v3 (Godot 4.5):
    header 112 bytes: GDPC | version 3 | 4,5,1 | flags 0x02 (relative file base)
                      | file_base | directory_offset | reserved
    payload: files, each aligned to 32 bytes
    directory: u32 count, then per file:
        u32 path_len, path bytes, u64 offset (from file_base), u64 size,
        md5[16], u32 flags

Usage:
    python art/pack_scenes.py <mod.pck> <scenes dir> <res:// prefix>
"""
from __future__ import annotations

import hashlib
import os
import struct
import sys
from pathlib import Path

HEADER_SIZE = 112
ALIGN = 32


def read_pck(path: Path) -> tuple[tuple[int, int, int], list[tuple[str, bytes]]]:
    data = path.read_bytes()
    if data[:4] != b"GDPC":
        raise SystemExit(f"{path} is not a Godot pack")
    version = struct.unpack_from("<I", data, 4)[0]
    if version != 3:
        raise SystemExit(f"unsupported pack version {version}")

    major, minor, patch, _flags = struct.unpack_from("<4I", data, 8)
    file_base, dir_offset = struct.unpack_from("<QQ", data, 24)

    count = struct.unpack_from("<I", data, dir_offset)[0]
    pos = dir_offset + 4
    entries: list[tuple[str, bytes]] = []
    for _ in range(count):
        path_len = struct.unpack_from("<I", data, pos)[0]
        pos += 4
        name = data[pos:pos + path_len].decode("utf-8").rstrip("\x00")
        pos += path_len
        ofs, size = struct.unpack_from("<QQ", data, pos)
        pos += 16 + 16 + 4
        entries.append((name, data[file_base + ofs:file_base + ofs + size]))
    return (major, minor, patch), entries


def write_pck(path: Path, version: tuple[int, int, int], entries: list[tuple[str, bytes]]) -> None:
    out = bytearray()
    out += b"GDPC"
    out += struct.pack("<I", 3)
    out += struct.pack("<4I", version[0], version[1], version[2], 0x02)
    out += struct.pack("<Q", HEADER_SIZE)
    dir_offset_pos = len(out)
    out += struct.pack("<Q", 0)  # patched below
    out += b"\x00" * (HEADER_SIZE - len(out))

    offsets: list[int] = []
    for _name, payload in entries:
        pad = (-len(out)) % ALIGN
        out += b"\x00" * pad
        offsets.append(len(out) - HEADER_SIZE)
        out += payload

    dir_offset = len(out)
    struct.pack_into("<Q", out, dir_offset_pos, dir_offset)

    out += struct.pack("<I", len(entries))
    for (name, payload), ofs in zip(entries, offsets):
        nb = name.encode("utf-8")
        out += struct.pack("<I", len(nb))
        out += nb
        out += struct.pack("<QQ", ofs, len(payload))
        out += hashlib.md5(payload).digest()
        out += struct.pack("<I", 0)

    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(out)
    os.replace(tmp, path)


def main() -> None:
    if len(sys.argv) != 4:
        raise SystemExit(__doc__)
    pck = Path(sys.argv[1])
    scene_dir = Path(sys.argv[2])
    prefix = sys.argv[3].strip("/")

    version, entries = read_pck(pck)
    existing = {name for name, _ in entries}

    added = 0
    for root, _dirs, files in os.walk(scene_dir):
        for f in sorted(files):
            full = Path(root) / f
            rel = full.relative_to(scene_dir).as_posix()
            name = f"{prefix}/{rel}"
            if name in existing:
                continue
            entries.append((name, full.read_bytes()))
            added += 1

    write_pck(pck, version, entries)
    print(f"pack_scenes: {pck.name} -> {len(entries)} files ({added} scenes added)")


if __name__ == "__main__":
    main()
