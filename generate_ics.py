#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DEFAULT_DATA = ROOT / "data" / "calendar-2026.json"
DEFAULT_OUTPUT = ROOT / "calendar-2026.ics"


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


def tibetan_day_short(display: str) -> str:
    # 例如：八月初五 -> 初五；十一月闰初三 -> 闰初三。
    return display.split("月", 1)[-1]


def summary_for(entry: dict) -> str:
    return tibetan_day_short(entry["tibetan"]["display"])


def location_for(entry: dict) -> str:
    notes = entry["notes"]
    gatherings = [note for note in notes if "荟供日" in note]
    merits = [note for note in notes if note.startswith("作何善恶成")]
    hair_days = [note for note in notes if note.startswith("理发吉日：")]
    specials = [
        note
        for note in notes
        if note not in gatherings
        and note not in merits
        and note not in hair_days
    ]
    lines = [f"藏历{entry['tibetan']['display']}"]
    lines.extend(gatherings)
    lines.extend(specials)
    lines.extend(merits)
    lines.extend(hair_days)
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
        f"X-WR-CALDESC:{ics_escape(payload['title'] + '（月视图显示藏历初几，日视图显示藏历详情）')}",
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
            f"LOCATION:{ics_escape(location_for(entry))}",
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
