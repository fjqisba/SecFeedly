#!/usr/bin/env python3
"""SecWeekly crawler: fetch RSS feeds and save structured articles to JSON."""

import json
import re
import html as html_mod
from datetime import datetime, timezone, timedelta
from pathlib import Path

import feedparser
import requests

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config" / "sources.json"
DATA_PATH = ROOT / "data" / "articles.json"


def load_config():
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


def load_existing():
    if DATA_PATH.exists():
        with open(DATA_PATH, encoding="utf-8") as f:
            return json.load(f)
    return []


def strip_html(text):
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = html_mod.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def estimate_read_time(text):
    words = len(text.split()) if text else 0
    return max(1, round(words / 200))


def parse_date(entry, fallback=None):
    for field in ("published_parsed", "updated_parsed"):
        tp = entry.get(field)
        if tp:
            try:
                return datetime(*tp[:6], tzinfo=timezone.utc)
            except Exception:
                pass
    if fallback:
        return fallback
    return datetime.now(timezone.utc)


def build_headers(settings, accept):
    return {
        "User-Agent": settings.get("user_agent", "SecWeekly-Bot/1.0"),
        "Accept": accept,
    }


def parse_feed(feed_url, settings):
    timeout = settings.get("request_timeout", 15)
    headers = build_headers(
        settings,
        "application/rss+xml, application/atom+xml, application/xml, text/xml, */*;q=0.5",
    )

    response = requests.get(feed_url, headers=headers, timeout=timeout)
    response.raise_for_status()
    return feedparser.parse(response.content)


def fetch_rss(source, settings):
    articles = []
    limit = settings.get("max_articles_per_source", 5)
    feed_url = source["url"]

    try:
        feed = parse_feed(feed_url, settings)
    except Exception as e:
        print(f"  [ERR] Failed to fetch {source['name']}: {e}")
        return articles

    if feed.bozo and not feed.entries:
        print(f"  [WARN] {source['name']}: feed parse error: {feed.bozo_exception}")
        return articles

    for entry in feed.entries[:limit]:
        title = strip_html(entry.get("title", ""))
        if not title:
            continue

        link = entry.get("link", "")
        summary = strip_html(entry.get("summary", entry.get("description", entry.get("content", [{}])[0].get("value", "") if entry.get("content") else "")))
        # Clean Reddit noise
        summary = re.sub(r"submitted by\s+/u/\S+\s*\[link\]\s*\[comments\]", "", summary).strip()
        summary = re.sub(r"\s+", " ", summary).strip()
        if not summary or len(summary) < 20:
            summary = title
        if len(summary) > 300:
            summary = summary[:297] + "..."

        pub_date = parse_date(entry)

        articles.append({
            "id": 0,
            "title": title,
            "source": source["name"],
            "source_icon": source["icon"],
            "url": link,
            "summary": summary,
            "tags": guess_tags(title, summary),
            "date": pub_date.strftime("%Y-%m-%d"),
            "read_time": estimate_read_time(summary),
        })

    print(f"  [OK] {source['name']}: {len(articles)} articles")
    return articles


SECURITY_KEYWORDS = {
    "逆向": ["逆向工具", "反编译"],
    "Ghidra": ["逆向工具", "反编译"],
    "IDA": ["逆向工具", "反编译"],
    "Binary Ninja": ["逆向工具", "反编译"],
    "反编译": ["逆向工具", "反编译"],
    "脱壳": ["逆向工具", "反编译"],
    "混淆": ["代码保护"],
    "Frida": ["动态插桩", "Hook"],
    "Hook": ["动态插桩", "Hook"],
    "Stalker": ["动态插桩", "Hook"],
    "CVE": ["漏洞分析", "CVE"],
    "漏洞": ["漏洞分析"],
    "RCE": ["漏洞分析", "RCE"],
    "0day": ["漏洞分析", "漏洞利用"],
    "exploit": ["漏洞分析", "漏洞利用"],
    "rootkit": ["APT", "Rootkit"],
    "APT": ["APT", "威胁情报"],
    "恶意软件": ["恶意软件"],
    "malware": ["恶意软件"],
    "勒索": ["恶意软件"],
    "ransomware": ["恶意软件"],
    "UEFI": ["硬件安全", "UEFI"],
    "Secure Boot": ["硬件安全", "UEFI"],
    "DMA": ["硬件安全", "DMA"],
    "CTF": ["CTF"],
    "writeup": ["CTF"],
    "PWN": ["CTF", "PWN"],
    "越狱": ["iOS", "越狱"],
    "jailbreak": ["iOS", "越狱"],
    "iOS": ["iOS"],
    "Android": ["Android", "移动安全"],
    "Wireshark": ["网络分析"],
    "TLS": ["TLS", "协议分析"],
    "加密": ["密码学"],
    "解密": ["密码学"],
    "Unicorn": ["CPU模拟", "漏洞挖掘"],
    "QEMU": ["CPU模拟"],
    "调试": ["调试"],
    "WinDbg": ["调试"],
    "内核": ["内核", "Windows"],
    "Kernel": ["内核"],
    "Linux": ["Linux"],
    "Windows": ["Windows"],
    "LLVM": ["LLVM"],
    "Rust": ["Rust"],
    "Go": ["Go"],
    "AI": ["AI"],
    "LLM": ["AI", "LLM"],
    "安全": ["安全"],
}


def guess_tags(title, summary):
    text = f"{title} {summary}".lower()
    matched = []
    for kw, tags in SECURITY_KEYWORDS.items():
        if kw.lower() in text:
            for t in tags:
                if t not in matched:
                    matched.append(t)
    if not matched:
        matched.append("安全")
    return matched[:4]


def deduplicate(articles, existing_urls):
    seen = set(existing_urls)
    result = []
    for a in articles:
        if a["url"] and a["url"] in seen:
            continue
        seen.add(a["url"])
        result.append(a)
    return result


def main():
    print("=== SecWeekly Crawler ===\n")
    config = load_config()
    settings = config.get("settings", {})
    sources = config.get("rss", [])

    existing = load_existing()
    existing_urls = {a["url"] for a in existing if a.get("url")}
    print(f"Loaded {len(existing)} existing articles\n")

    all_new = []
    for src in sources:
        articles = fetch_rss(src, settings)
        all_new.extend(articles)

    new_unique = deduplicate(all_new, existing_urls)
    print(f"\nNew unique articles: {len(new_unique)}")

    max_age = settings.get("max_age_days", 7)
    cutoff = datetime.now(timezone.utc) - timedelta(days=max_age)
    merged = new_unique + existing
    merged = [a for a in merged if datetime.fromisoformat(a["date"]).replace(tzinfo=timezone.utc) >= cutoff]

    merged.sort(key=lambda a: a["date"], reverse=True)

    max_total = settings.get("max_total_articles", 50)
    merged = merged[:max_total]

    for i, a in enumerate(merged):
        a["id"] = i + 1

    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)

    print(f"Total articles saved: {len(merged)}")
    print("Done.")


if __name__ == "__main__":
    main()
