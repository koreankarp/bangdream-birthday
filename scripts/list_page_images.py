#!/usr/bin/env python3
"""주어진 문서의 이미지 alt / URL 을 전부 나열한다.

용도: 특정 밴드의 '로고만 있는' 원판 이미지를 직접 골라내기 위한 탐색용.
사용법: python3 scripts/list_page_images.py <URL> [<URL> ...] [--filter 키워드]
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from collect_band_logos import IMG_PATTERN, fetch  # noqa: E402


def main() -> None:
    args = sys.argv[1:]
    keyword = None
    if "--filter" in args:
        index = args.index("--filter")
        keyword = args[index + 1].lower()
        args = args[:index] + args[index + 2 :]

    if not args:
        print(__doc__)
        sys.exit(2)

    for page in args:
        print(f"\n===== {page}")
        try:
            html = fetch(page).decode("utf-8", errors="replace")
        except Exception as error:  # noqa: BLE001
            print(f"  실패: {error}")
            continue

        seen: set[str] = set()
        for match in IMG_PATTERN.finditer(html):
            src, alt = match.group(1), match.group(2)
            if src in seen:
                continue
            seen.add(src)
            if keyword and keyword not in alt.lower():
                continue
            print(f"  alt={alt!r:46} https:{src}")


if __name__ == "__main__":
    main()
