#!/usr/bin/env python3
"""bands.json + data/birthdays/*.json -> src/data/characters.json

밴드 명단(60명)을 기준으로 삼고, 수집된 생일 파일을 id로 조인한다.
생일이 없는 캐릭터도 birthday: null 로 반드시 포함시킨다 — 앱에서 '미공개'로 표시한다.
"""

from __future__ import annotations

import glob
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BANDS = ROOT / "data" / "bands.json"
BIRTHDAY_DIR = ROOT / "data" / "birthdays"
OUT = ROOT / "src" / "data" / "characters.json"
IMAGE_DIR = ROOT / "public" / "characters"
IMAGE_HD_DIR = ROOT / "public" / "characters-hd"
LOGO_DIR = ROOT / "public" / "bands"
LOGO_EXTENSIONS = ("svg", "webp", "png", "jpg", "gif")

MMDD = re.compile(r"^(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$")
VALID_CONFIDENCE = {"official", "secondary", "unknown"}

# 수집 에이전트가 표기를 조금씩 달리 쓰기 때문에 원본 파일은 그대로 두고 여기서 정규화한다.
CONFIDENCE_ALIASES = {
    "primary": "official",
    "game": "official",
    "in-game": "official",
    "anime": "official",
    "wiki": "secondary",
    "fan": "secondary",
    "": "unknown",
    None: "unknown",
}


def normalize_confidence(raw: str | None) -> str:
    if raw in CONFIDENCE_ALIASES:
        return CONFIDENCE_ALIASES[raw]
    value = str(raw).strip().lower()
    return CONFIDENCE_ALIASES.get(value, value)


# bands.json 의 id 를 정본으로 두고, 수집 쪽에서 다른 로마자 표기를 쓴 경우만 여기서 흡수한다.
ID_ALIASES = {
    "satou-masuki": "satou-masaki",
}


def load_birthdays() -> dict[str, dict]:
    """수집 파일을 읽어 characterId -> record 로 펼친다."""
    merged: dict[str, dict] = {}
    for path in sorted(glob.glob(str(BIRTHDAY_DIR / "*.json"))):
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        for entry in payload.get("characters", []):
            cid = entry.get("id")
            if not cid:
                continue
            cid = ID_ALIASES.get(cid, cid)
            birthday = entry.get("birthday")
            confidence = normalize_confidence(entry.get("confidence"))
            source_name = entry.get("sourceName") or ""

            if birthday is not None and not MMDD.match(str(birthday)):
                raise ValueError(f"{path}: {cid} 의 birthday 형식이 MM-DD가 아님: {birthday!r}")
            if confidence not in VALID_CONFIDENCE:
                raise ValueError(f"{path}: {cid} 의 confidence 값이 예상 밖: {confidence!r}")
            if birthday is None and confidence != "unknown":
                raise ValueError(f"{path}: {cid} 는 생일이 없는데 confidence가 {confidence!r}")

            if cid in merged:
                prev = merged[cid]
                if prev.get("birthday") != birthday:
                    raise ValueError(
                        f"{cid} 생일이 파일 간 불일치: {prev.get('birthday')!r} vs {birthday!r}"
                    )
                continue

            merged[cid] = {
                "birthday": birthday,
                "confidence": confidence,
                "sourceName": source_name or None,
                "sourceUrl": entry.get("sourceUrl") or None,
            }
    return merged


def band_logo(band_id: str) -> str | None:
    """collect_band_logos.py 가 실제 포맷에 맞는 확장자로 저장하므로 여기서 찾아 붙인다."""
    for extension in LOGO_EXTENSIONS:
        if (LOGO_DIR / f"{band_id}.{extension}").exists():
            return f"/bands/{band_id}.{extension}"
    return None


def main() -> None:
    bands_payload = json.loads(BANDS.read_text(encoding="utf-8"))
    birthdays = load_birthdays()

    characters: list[dict] = []
    bands: list[dict] = []
    seen_ids: set[str] = set()

    for band in bands_payload["bands"]:
        bands.append(
            {
                "id": band["id"],
                "name": band["name"],
                "category": band["category"],
                "logo": band_logo(band["id"]),
            }
        )
        for member in band["members"]:
            cid = member["id"]
            if cid in seen_ids:
                raise ValueError(f"중복 캐릭터 id: {cid}")
            seen_ids.add(cid)

            found = birthdays.get(cid, {})
            image = f"/characters/{cid}.webp"
            image_hd = f"/characters-hd/{cid}.webp"
            characters.append(
                {
                    "id": cid,
                    "nameKo": member["nameKo"],
                    "stageName": member.get("stageName"),
                    "bandId": band["id"],
                    "bandName": band["name"],
                    "roles": member["roles"],
                    "birthday": found.get("birthday"),
                    "confidence": found.get("confidence", "unknown"),
                    "sourceName": found.get("sourceName"),
                    "sourceUrl": found.get("sourceUrl"),
                    # 목록(티켓)은 썸네일, 패스 카드는 고해상도를 쓴다.
                    "image": image if (IMAGE_DIR / f"{cid}.webp").exists() else None,
                    "imageHd": image_hd if (IMAGE_HD_DIR / f"{cid}.webp").exists() else None,
                }
            )

    unknown = [c["id"] for c in characters if c["birthday"] is None]
    extra = sorted(set(birthdays) - seen_ids)
    if extra:
        raise ValueError(f"밴드 명단에 없는 캐릭터의 생일 데이터: {extra}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(
            {
                "generatedAt": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
                "bands": bands,
                "characters": characters,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print(f"characters: {len(characters)}  생일 확보: {len(characters) - len(unknown)}  미확보: {len(unknown)}")
    if unknown:
        print("  미확보 ->", ", ".join(unknown))
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
