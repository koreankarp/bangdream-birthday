#!/usr/bin/env python3
"""밴드 로고 이미지를 수집해 public/bands/<bandId>.webp 로 저장한다.

나무위키의 BanG Dream 문서 하단 네비게이션 틀에는 12밴드 로고가 한 번에 들어 있어서,
문서 하나만 받아도 전부 추출할 수 있다. 이미지 자체의 권리는 원저작자에게 있으므로
공개 배포 전에 반드시 확인해야 한다 (data/band-logos.json 의 note 에도 남긴다).
"""

from __future__ import annotations

import json
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BANDS = ROOT / "data" / "bands.json"
OUT_DIR = ROOT / "public" / "bands"
MANIFEST = ROOT / "data" / "band-logos.json"

SOURCE_PAGE = "https://namu.wiki/w/Roselia"
UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)

# 네비게이션 틀의 로고가 원판이 아닌 밴드는 여기서 직접 지정한다.
# 12개를 직접 눈으로 확인한 결과 아래 셋이 문제였다.
# - hello-happy-world: 틀에 실린 것이 한국어판('헬로, 해피 월드!')이라 일본어 원판으로 교체.
# - mugendai-mewtype:  틀에 실린 것이 한국어판('무겐다이 뮤타입')이라 일본어 원판으로 교체.
# - ikka-dumb-rock:   틀에 실린 것이 멤버 5인이 들어간 아트워크이고, 밴드 문서의 한국어판
#                     로고('일가 DumbRock!') 대신 로고만 있는 원판('Ikka DumbRock!')을 쓴다.
LOGO_OVERRIDES: dict[str, str] = {
    "hello-happy-world": (
        "https://i.namu.wiki/i/bPYhb8PyIAn0FQsKzJK8EknyRZHUbYmW7kKaS3feHdp9_2fmFBTcM8ol"
        "7r8O0CtZqLVbnbFWnrqmeaesgvBDB5GCRRetz2HjE2oZSiDNgf3acV79LfuKmmJyCPJxz1uLqhkBbO"
        "yra_J10FOuK_ZY7Q.webp"
    ),
    "mugendai-mewtype": (
        "https://i.namu.wiki/i/j1WDVdZ1v2uaZo39y5l2k9kCoRxnVvC2Mq3xlHU6xGJBycmnIIKQQdo2"
        "U1D6Lrgohn_tYFXYC4B1a6bAve3UbAmVq5mFZ_a1hNNwFv8HOGIhbnS5B1M5WbgUc75cnYzYkg3kap"
        "zZgy7my2MdngiNcQ.webp"
    ),
    "ikka-dumb-rock": (
        "https://i.namu.wiki/i/JwqsXqu77BDIeZbEsUAkzH8HLAUO0sDq4_C5w1sYUV2JMBu6aiUL8z-K"
        "-mX7sa5PrlskUwwM7HMh13FaVVu_cKWwYlKVupR1MXpfXMNlqb_LVHc-rB3HYZQQDxEcHXGxnPawcF"
        "yN41J7JKk5xeZBHg.webp"
    ),
}

# alt 텍스트에서 밴드를 알아내기 위한 키워드. 위에서부터 먼저 맞는 것을 쓴다.
BAND_KEYWORDS: list[tuple[str, tuple[str, ...]]] = [
    ("poppin-party", ("poppin",)),
    ("afterglow", ("afterglow",)),
    ("pastel-palettes", ("pastel",)),
    ("roselia", ("roselia",)),
    ("hello-happy-world", ("hello happy", "hello_happy", "happy world", "hellohappy")),
    ("morfonica", ("morfonica",)),
    ("raise-a-suilen", ("raise a suilen", "raise_a_suilen", "suilen")),
    ("mygo", ("mygo",)),
    ("ave-mujica", ("ave mujica", "avemujica")),
    ("mugendai-mewtype", ("mewtype", "yumemita")),
    ("millsage", ("millsage",)),
    ("ikka-dumb-rock", ("ikkadumbrock", "ikka dumb", "dumbrock", "dumb rock")),
]

IMG_PATTERN = re.compile(
    r"""src=['"](//i\.namu\.wiki/i/[^'"]+)['"][^>]*?alt=['"]([^'"]*)['"]"""
)


def detect_extension(data: bytes) -> str:
    """실제 바이트로 포맷을 판별한다.

    나무위키 이미지 URL 은 확장자가 .webp 여도 내용이 SVG/PNG 인 경우가 있다.
    확장자를 그대로 믿고 저장하면 서버가 엉뚱한 Content-Type 을 붙여 렌더가 깨진다.
    """
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    if data[:3] == b"\xff\xd8\xff":
        return "jpg"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return "gif"
    head = data[:400].lstrip()
    if head[:5] == b"<?xml" or head[:4] == b"<svg" or b"<svg" in data[:400]:
        return "svg"
    raise ValueError("알 수 없는 이미지 포맷")


def fetch(url: str) -> bytes:
    # 문서 제목에 한글·일본어·공백이 들어가면 그대로는 요청할 수 없으므로 인코딩한다.
    safe_url = urllib.parse.quote(url, safe=":/?&=#%+,!~*'()")
    request = urllib.request.Request(safe_url, headers={"User-Agent": UA})
    with urllib.request.urlopen(request, timeout=40) as response:
        return response.read()


def band_for(alt: str) -> str | None:
    lowered = alt.lower()
    for band_id, keywords in BAND_KEYWORDS:
        if any(keyword in lowered for keyword in keywords):
            return band_id
    return None


def pick_best(candidates: list[tuple[str, str]]) -> tuple[str, str]:
    """(alt, src) 후보 중 기본 로고를 고른다.

    같은 밴드에 10주년 기념 로고가 함께 실려 있어서, 'logo' 가 들어가고
    '10th' 가 없는 것을 최우선으로 삼는다.
    """
    plain_logo = [c for c in candidates if "logo" in c[0].lower() and "10th" not in c[0].lower()]
    if plain_logo:
        return plain_logo[0]
    without_anniversary = [c for c in candidates if "10th" not in c[0].lower()]
    if without_anniversary:
        return without_anniversary[0]
    return candidates[0]


def main() -> None:
    band_ids = [band["id"] for band in json.loads(BANDS.read_text(encoding="utf-8"))["bands"]]

    print(f"fetching {SOURCE_PAGE}")
    html = fetch(SOURCE_PAGE).decode("utf-8", errors="replace")

    found: dict[str, list[tuple[str, str]]] = {}
    for match in IMG_PATTERN.finditer(html):
        src, alt = match.group(1), match.group(2)
        band_id = band_for(alt)
        if band_id is None:
            continue
        entries = found.setdefault(band_id, [])
        if (alt, src) not in entries:
            entries.append((alt, src))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    records = []
    missing = []

    for band_id in band_ids:
        override = LOGO_OVERRIDES.get(band_id)
        if override:
            alt, url = "(override) 원판 로고 직접 지정", override
        else:
            candidates = found.get(band_id)
            if not candidates:
                missing.append(band_id)
                print(f"  {band_id:20} MISSING — alt 매칭 실패")
                continue
            alt, src = pick_best(candidates)
            url = "https:" + src

        data = fetch(url)
        extension = detect_extension(data)
        target = OUT_DIR / f"{band_id}.{extension}"
        target.write_bytes(data)
        records.append(
            {
                "bandId": band_id,
                "localPath": f"/bands/{band_id}.{extension}",
                "format": extension,
                "sourceAlt": alt,
                "sourceImage": url,
                "byteSize": len(data),
            }
        )
        print(f"  {band_id:20} {extension:4} {len(data):>7}B  alt={alt!r}")

    MANIFEST.write_text(
        json.dumps(
            {
                "collectedAt": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
                "sourcePage": SOURCE_PAGE,
                "note": (
                    "나무위키 BanG Dream 문서의 네비게이션 틀에서 추출한 밴드 로고. "
                    "이미지 권리는 원저작자(BanG Dream! Project / Bushiroad)에게 있으므로 "
                    "공개 배포 전에 반드시 권리를 확인해야 한다."
                ),
                "logos": records,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print(f"\n수집 {len(records)}/{len(band_ids)} · wrote {MANIFEST}")
    if missing:
        print("미수집:", ", ".join(missing))
        sys.exit(1)


if __name__ == "__main__":
    main()
