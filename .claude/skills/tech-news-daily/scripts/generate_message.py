#!/usr/bin/env python3
"""
Daily Tech Brief - 카톡 공유 산출물 생성기

입력: data/YYYY-MM-DD.json
출력: Message/YYYY-MM-DD/card.png + Message/YYYY-MM-DD/text.txt

사용법:
    python3 .claude/skills/tech-news-daily/scripts/generate_message.py data/2026-05-26.json

의존성: playwright (이미 설치됨)
"""
import json
import sys
from pathlib import Path

SITE_URL = "https://kimpaulie.github.io/kaisttechbreif/"
PROJECT_ROOT = Path(__file__).resolve().parents[4]   # /Users/cheil/dev/technews
TEMPLATE = Path(__file__).resolve().parents[1] / "templates" / "kakao-card.html"
OUTPUT_BASE = PROJECT_ROOT / "Message"


def build_text(edition: dict) -> str:
    """카톡 복붙용 텍스트 생성."""
    date_str = edition["id"].replace("-", ".")
    dow = edition.get("dayOfWeek", "")
    vol = edition.get("volumeNumber", "")
    coverage = (edition.get("coverage") or {}).get("label")

    head = f"📰 데일리 테크 브리프 Vol.{vol}\n{date_str} {dow}요일"
    if coverage:
        head += f" (다룬 기간: {coverage})"

    lines = [head, ""]
    for item in edition["newsItems"]:
        lines.append(f"{item['order']:02d}. {item['title']}")
    lines.append("")
    lines.append(f"전체 보기 👉 {SITE_URL}#{edition['id']}")
    return "\n".join(lines)


def generate_card_png(edition: dict, out_path: Path) -> None:
    """Playwright로 9:16 카드 PNG 생성."""
    from playwright.sync_api import sync_playwright

    template_url = TEMPLATE.resolve().as_uri()

    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(viewport={"width": 1080, "height": 1920}, device_scale_factor=2)
        page = ctx.new_page()
        page.goto(template_url, wait_until="networkidle")
        page.evaluate("ed => window.renderEdition(ed)", edition)
        # 폰트 적용 대기 (Pretendard / Inter)
        page.wait_for_timeout(500)
        page.screenshot(path=str(out_path), full_page=False, type="png")
        browser.close()


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: generate_message.py <path-to-edition-json>", file=sys.stderr)
        return 1

    json_path = Path(sys.argv[1]).resolve()
    if not json_path.is_file():
        print(f"Not found: {json_path}", file=sys.stderr)
        return 1

    edition = json.loads(json_path.read_text(encoding="utf-8"))
    out_dir = OUTPUT_BASE / edition["id"]
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1) 텍스트
    text_path = out_dir / "text.txt"
    text_path.write_text(build_text(edition), encoding="utf-8")
    print(f"✓ wrote {text_path.relative_to(PROJECT_ROOT)}")

    # 2) 이미지
    card_path = out_dir / "card.png"
    generate_card_png(edition, card_path)
    print(f"✓ wrote {card_path.relative_to(PROJECT_ROOT)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
