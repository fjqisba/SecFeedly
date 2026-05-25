#!/usr/bin/env python3
"""Generate index.html by injecting article data into the template."""

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_PATH = ROOT / "template.html"
DATA_PATH = ROOT / "data" / "articles.json"
OUTPUT_PATH = ROOT / "index.html"


def main():
    print("=== SecWeekly Page Generator ===\n")

    with open(TEMPLATE_PATH, encoding="utf-8") as f:
        template = f.read()

    articles = []
    if DATA_PATH.exists():
        with open(DATA_PATH, encoding="utf-8") as f:
            articles = json.load(f)
    print(f"Loaded {len(articles)} articles")

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    data_json = json.dumps(articles, ensure_ascii=False)

    html = template.replace("__DATA_PLACEHOLDER__", data_json)
    html = html.replace("__DATE__", today)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Generated {OUTPUT_PATH} ({len(html)} bytes)")
    print("Done.")


if __name__ == "__main__":
    main()
