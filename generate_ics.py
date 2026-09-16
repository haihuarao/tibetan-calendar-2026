#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DEFAULT_DATA = ROOT / "data" / "calendar-2026.json"
DEFAULT_OUTPUT = ROOT / "calendar-2026.ics"

WEEKDAYS = "一二三四五六日"
GENERIC_NOTES = {"十斋日", "飞幡日"}
MONTH_LABELS = {
    "庄严月", "满意月", "神变月", "苦行月", "具香月", "萨嘎月",
    "作净月", "明净月", "具醉月", "具贤月", "天降月", "持众月",
}


def ics_escape(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace("\r\n", "\n")
        .replace("\r", "\n")
        .replace("\n", "\\n")
        .replace(";", "\\;")
        .replace(",", "\\,")
    )


def fold_line(line: str, limit: int = 75) -> list[str]:
    if not line:
        return [""]
    chunks: list[str] = []
    current = ""
    for char in line:
        candidate = current + char
        if current and len(candidate.encode("utf-8")) > limit:
            chunks.append(current)
            current = " " + char
        else:
            current = candidate
    chunks.append(current)
    return chunks


def summary_for(entry: dict) -> str:
    summary = (
        f"藏历{entry['tibetan']['display']} · "
        f"农历{entry['lunar']['display']}"
    )
    candidates = [
        note
        for note in entry["notes"]
        if note not in GENERIC_NOTES
        and note not in MONTH_LABELS
        and not note.startswith("理发吉日：")
        and not note.startswith("作何善恶成")
    ]
    if candidates:
        summary += "｜" + "、".join(candidates[:2])
    elif "十斋日" in entry["notes"]:
        summary += "｜十斋日"
    elif "飞幡日" in entry["notes"]:
        summary += "｜飞幡日"
    return summary


def description_for(entry: dict) -> str:
    date = dt.date.fromisoformat(entry["date"])
    lines = [
        f"公历：{date.year}年{date.month}月{date.day}日 星期{WEEKDAYS[date.weekday()]}",
        f"藏历火马年：{entry['tibetan']['display']}",
        f"藏历月名：{entry['tibetan']['month_name']}",
        f"农历丙午年：{entry['lunar']['display']}",
    ]
    if entry["tibetan"].get("previous_day_skipped"):
        lines.append("藏历备注：前一日为缺日")
    if entry["notes"]:
        lines.append("事项：")
        lines.extend(entry["notes"])
    lines.append("来源：2026（农历）藏历火马年月历.pdf")
    return "\n".join(lines)


def build_calendar(data_path: Path, output_path: Path) -> None:
    payload = json.loads(data_path.read_text(encoding="utf-8"))
    entries = payload["entries"]
    if len(entries) != 365:
        raise ValueError(f"Expected 365 entries, got {len(entries)}")

    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//M.R Bao//2026 Tibetan Calendar//CN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:2026 藏历火马年",
        f"X-WR-CALDESC:{ics_escape(payload['title'] + '（公历、农历、藏历对照，来源为用户提供的月历 PDF）')}",
        "X-WR-TIMEZONE:Asia/Shanghai",
        "X-PUBLISHED-TTL:PT1H",
        "REFRESH-INTERVAL;VALUE=DURATION:PT1H",
        "X-APPLE-CALENDAR-COLOR:#C24B2A",
    ]

    for entry in entries:
        start = dt.date.fromisoformat(entry["date"])
        end = start + dt.timedelta(days=1)
        uid = f"tibetan-2026-{start:%Y%m%d}@tibetan-calendar.local"
        event_lines = [
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTAMP:{stamp}",
            f"DTSTART;VALUE=DATE:{start:%Y%m%d}",
            f"DTEND;VALUE=DATE:{end:%Y%m%d}",
            f"SUMMARY:{ics_escape(summary_for(entry))}",
            f"DESCRIPTION:{ics_escape(description_for(entry))}",
            "TRANSP:TRANSPARENT",
            "SEQUENCE:0",
            "END:VEVENT",
        ]
        lines.extend(event_lines)

    lines.append("END:VCALENDAR")
    output = "\r\n".join(
        folded
        for line in lines
        for folded in fold_line(line)
    ) + "\r\n"
    output_path.write_bytes(output.encode("utf-8"))
    print(f"Wrote {len(entries)} all-day events to {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    build_calendar(args.data, args.output)


if __name__ == "__main__":
    main()
