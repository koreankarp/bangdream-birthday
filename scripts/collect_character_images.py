#!/usr/bin/env python3
"""캐릭터 고해상도 초상화를 public/characters-hd/ 로 수집한다.

기존 public/characters/ 의 이미지는 나무위키 og:image 썸네일(200x254)이라
패스 카드(152px, 고DPI 에서 300px 이상)에서 뿌옇게 보인다. 캐릭터 문서 본문에는
같은 그림의 1000x1272 원본이 실려 있어서 그것을 따로 받아 카드에서만 쓴다.

목록(티켓)은 계속 저화질을 쓴다 — 60장을 모두 고화질로 깔면 목록이 무거워진다.

사용법: python3 scripts/collect_character_images.py [--limit N] [--only <id>]
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from collect_band_logos import IMG_PATTERN, detect_extension, fetch  # noqa: E402
from inspect_band_logos import webp_size  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
BANDS = ROOT / "data" / "bands.json"
OUT_DIR = ROOT / "public" / "characters-hd"
MANIFEST = ROOT / "data" / "character-images-hd.json"

# 기존 썸네일과 같은 프레이밍인지 판단하는 기준.
# og:image 는 200x254(구작) / 200x240(신작) 이므로 그 근방만 받아들인다.
MIN_WIDTH = 500
RATIO_MIN = 0.70
RATIO_MAX = 0.88

# 초상화가 아닌 것이 확실한 이미지는 후보에서 뺀다.
SKIP_ALT_HINTS = ("logo", "로고", "10th", "sd버전", "signature", "사인")

# 문서 상단 네비게이션 틀에 12밴드 이미지가 먼저 깔려서 후보 앞자리를 차지한다.
# 신규 밴드 캐릭터는 초상화가 그 뒤로 밀리므로 예산을 넉넉히 준다.
CANDIDATE_BUDGET = 34


def is_portrait(width: int, height: int) -> bool:
    return width >= MIN_WIDTH and RATIO_MIN <= width / height <= RATIO_MAX


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0, help="앞에서 N명만 처리 (시험용)")
    parser.add_argument("--only", default="", help="특정 캐릭터 id 만 처리")
    parser.add_argument(
        "--missing",
        action="store_true",
        help="아직 고해상도 파일이 없는 캐릭터만 처리 (기존 매니페스트에 이어붙인다)",
    )
    args = parser.parse_args()

    payload = json.loads(BANDS.read_text(encoding="utf-8"))
    characters = [
        {"id": member["id"], "nameKo": member["nameKo"], "bandId": band["id"]}
        for band in payload["bands"]
        for member in band["members"]
    ]
    if args.only:
        characters = [c for c in characters if c["id"] == args.only]
    if args.missing:
        characters = [c for c in characters if not (OUT_DIR / f"{c['id']}.webp").exists()]
    if args.limit:
        characters = characters[: args.limit]

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # --missing 으로 이어서 돌릴 때 이전 수집 기록을 잃지 않는다.
    records: list[dict] = []
    if args.missing and MANIFEST.exists():
        records = json.loads(MANIFEST.read_text(encoding="utf-8")).get("images", [])

    failures: list[str] = []

    for index, character in enumerate(characters, start=1):
        cid, name = character["id"], character["nameKo"]
        page = f"https://namu.wiki/w/{name}"

        try:
            html = fetch(page).decode("utf-8", errors="replace")
        except Exception as error:  # noqa: BLE001
            print(f"[{index:2}/{len(characters)}] {cid:20} 문서 실패: {error}")
            failures.append(cid)
            continue

        # 페이지 순서를 유지한다 — 상단 정보상자의 초상화가 먼저 나온다.
        candidates: list[tuple[str, str]] = []
        seen: set[str] = set()
        for match in IMG_PATTERN.finditer(html):
            src, alt = match.group(1), match.group(2)
            if src in seen:
                continue
            seen.add(src)
            lowered = alt.lower()
            if any(hint in lowered for hint in SKIP_ALT_HINTS):
                continue
            if src.endswith(".svg"):
                continue
            candidates.append((alt, src))

        chosen = None
        for alt, src in candidates[:CANDIDATE_BUDGET]:
            try:
                data = fetch("https:" + src)
                extension = detect_extension(data)
            except Exception:  # noqa: BLE001
                continue
            if extension != "webp":
                continue

            temp = OUT_DIR / f".probe-{cid}.webp"
            temp.write_bytes(data)
            size = webp_size(temp)
            temp.unlink(missing_ok=True)
            if not size or not is_portrait(*size):
                continue

            chosen = (alt, src, data, size)
            break

        if not chosen:
            print(f"[{index:2}/{len(characters)}] {cid:20} 초상화 후보 없음 (후보 {len(candidates)}개)")
            failures.append(cid)
            continue

        alt, src, data, size = chosen
        target = OUT_DIR / f"{cid}.webp"
        target.write_bytes(data)
        records.append(
            {
                "characterId": cid,
                "characterName": name,
                "bandId": character["bandId"],
                "localPath": f"/characters-hd/{cid}.webp",
                "width": size[0],
                "height": size[1],
                "sourcePage": page,
                "sourceImage": "https:" + src,
                "sourceAlt": alt,
                "byteSize": len(data),
            }
        )
        print(f"[{index:2}/{len(characters)}] {cid:20} {size[0]}x{size[1]} {len(data):>7}B  alt={alt!r}")

        # 나무위키에 과한 부담을 주지 않도록 약간 쉬어 간다.
        time.sleep(0.4)

    MANIFEST.write_text(
        json.dumps(
            {
                "collectedAt": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
                "note": (
                    "패스 카드용 고해상도 초상화. 목록(티켓)은 public/characters/ 의 "
                    "썸네일을 계속 쓴다. 이미지 권리는 원저작자에게 있다."
                ),
                "images": records,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print(f"\n수집 {len(records)}/{len(characters)} · wrote {MANIFEST}")
    if failures:
        print("미수집:", ", ".join(failures))


if __name__ == "__main__":
    main()
