"""测试用的图片生成工具函数（不含 fixture）。"""

from __future__ import annotations

import struct
import zlib
from pathlib import Path


def make_png(w: int, h: int) -> bytes:
    """生成指定宽高的最小合法 PNG 字节串。"""
    sig = b"\x89PNG\r\n\x1a\n"

    def chunk(name: bytes, data: bytes) -> bytes:
        length = struct.pack(">I", len(data))
        crc = struct.pack(">I", zlib.crc32(name + data) & 0xFFFFFFFF)
        return length + name + data + crc

    ihdr_data = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    raw = b"".join(b"\x00" + b"\x00" * (w * 3) for _ in range(h))
    compressed = zlib.compress(raw)
    return sig + chunk(b"IHDR", ihdr_data) + chunk(b"IDAT", compressed) + chunk(b"IEND", b"")


def make_jpeg(w: int, h: int) -> bytes:
    """生成包含正确宽高信息的最小合法 JPEG 字节串。"""
    soi = b"\xff\xd8"
    app0 = b"\xff\xe0" + struct.pack(">H", 16) + b"JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
    sof0_data = struct.pack(">HBHHB", 11, 8, h, w, 1)
    sof0 = b"\xff\xc0" + sof0_data
    eoi = b"\xff\xd9"
    return soi + app0 + sof0 + eoi
