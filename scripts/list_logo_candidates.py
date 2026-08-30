#!/usr/bin/env python3
"""밴드별 로고 후보를 전부 나열한다 (한국어판 / 원판 구분용).

collect_band_logos.py 는 후보 중 하나만 고르는데, 어떤 밴드는 한국어 현지화 로고와
일본어 원판이 함께 실려 있다. 무엇을 고를지 판단하려면 후보 전체를 봐야 한다.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from collect_band_logos import (  # noqa: E402
    BAND_KEYWORDS,
    IMG_PATTERN,
    SOURCE_PAGE,
    band_for,
    fetch,
)

EXTRA_PAGES = [
    "https://namu.wiki/w/夢限大みゅーたいぷ",
    "https://namu.wiki/w/일가 Dumb Rock!",
]


def main() -> None:
    pages = [SOURCE_PAGE, *EXTRA_PAGES]
    found: dict[str, list[tuple[str, str, str]]] = {}

    for page in pages:
        print(f"# fetching {page}")
        try:
            html = fetch(page).decode("utf-8", errors="replace")
        except Exception as error:  # noqa: BLE001
            print(f"  실패: {error}")
            continue

        for match in IMG_PATTERN.finditer(html):
            src, alt = match.group(1), match.group(2)
            band_id = band_for(alt)
            if band_id is None:
                continue
            entries = found.setdefault(band_id, [])
            if not any(existing[1] == src for existing in entries):
                entries.append((alt, src, page))

    print()
    for band_id, _ in BAND_KEYWORDS:
        candidates = found.get(band_id, [])
        print(f"== {band_id}  ({len(candidates)}개)")
        for alt, src, page in candidates:
            tail = src.rsplit("/", 1)[-1][:26]
            print(f"   alt={alt!r:44} …{tail}")


if __name__ == "__main__":
    main()
