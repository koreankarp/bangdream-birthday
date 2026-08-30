#!/usr/bin/env python3
"""수집한 밴드 로고의 크기·가로세로비·밝기를 점검한다.

어두운 테마 위에 올리기 때문에, 불투명 픽셀의 평균 밝기가 낮은 로고는
그대로 두면 배경에 묻힌다. 그런 로고를 골라내기 위한 진단 스크립트.
Pillow 가 없으면 크기만 보고한다.
"""

from __future__ import annotations

import struct
import sys
from pathlib import Path

BANDS_DIR = Path(__file__).resolve().parent.parent / "public" / "bands"

try:
    from PIL import Image  # type: ignore

    HAS_PIL = True
except ImportError:
    HAS_PIL = False


def webp_size(path: Path) -> tuple[int, int] | None:
    """VP8/VP8L/VP8X 헤더에서 크기만 읽는다 (Pillow 없을 때의 대비책)."""
    data = path.read_bytes()
    if data[:4] != b"RIFF" or data[8:12] != b"WEBP":
        return None
    chunk = data[12:16]
    if chunk == b"VP8X":
        width = int.from_bytes(data[24:27], "little") + 1
        height = int.from_bytes(data[27:30], "little") + 1
        return width, height
    if chunk == b"VP8 ":
        width, height = struct.unpack("<HH", data[26:30])
        return width & 0x3FFF, height & 0x3FFF
    if chunk == b"VP8L":
        bits = int.from_bytes(data[21:25], "little")
        return (bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1
    return None


def main() -> None:
    # 인자로 파일 경로가 주어지면 그 파일들만 본다 (후보 이미지 비교용).
    paths = [Path(arg) for arg in sys.argv[1:]] or sorted(BANDS_DIR.glob("*"))

    for path in paths:
        if not path.is_file():
            continue
        size = webp_size(path)
        label = f"{path.name:26}"

        if not HAS_PIL:
            ratio = f"{size[0] / size[1]:.2f}" if size else "?"
            print(f"{label} {str(size):14} 비율 {ratio:5} {path.stat().st_size:>7}B  (Pillow 없음)")
            continue

        with Image.open(path) as image:
            rgba = image.convert("RGBA")
            width, height = rgba.size
            pixels = list(rgba.getdata())

        visible = [p for p in pixels if p[3] > 40]
        if not visible:
            print(f"{label} {width}x{height}  불투명 픽셀 없음")
            continue

        luma = sum(0.2126 * r + 0.7152 * g + 0.0722 * b for r, g, b, _ in visible) / len(visible)
        transparent_ratio = 1 - len(visible) / len(pixels)
        verdict = "어두움 — 다크배경에 묻힘" if luma < 90 else "밝음 OK"
        print(
            f"{label} {width}x{height}  비율 {width / height:.2f}  "
            f"평균밝기 {luma:5.1f}  투명 {transparent_ratio * 100:4.1f}%  {verdict}"
        )


if __name__ == "__main__":
    main()
