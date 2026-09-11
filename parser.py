"""Parser for the documented bracketed TXT export format; no network access."""
from datetime import datetime
from pathlib import Path
import re

import pandas as pd

HEADER = re.compile(r"^\[(\d{2}\.\d{2}\.\d{4} \d{1,2}:\d{2}(?::\d{2})?)\]\s+([^:\r\n]+):( ?)(.*)$")
DATED_LINE = re.compile(r"^\[\d{2}\.\d{2}\.\d{4}\s+\d{1,2}:\d{2}")
# Exact markers only: ordinary words such as 'фото' or 'стикер' are research text.
MEDIA_MARKERS = {
    "<media omitted>", "<медиафайлы отсутствуют>",
    "[голосовое сообщение]", "[voice message]", "[аудиосообщение]",
    "[изображение]", "[фотография]", "[photo]", "[image]",
    "[стикер]", "[sticker]", "[видео]", "[video]",
}
SERVICE_MARKERS = {"--- начало экспорта ---", "--- конец экспорта ---"}
COLUMNS = ["message_id", "datetime", "author", "text", "is_reply",
           "reply_to_author", "source_file", "quoted_text", "_turn_id"]


def parse_chat(path: str) -> pd.DataFrame:
    """Read UTF-8 (including BOM) or Windows-1251. Keep original file order.

    Extra columns preserve quoted material for audit and participant changes
    across excluded non-text messages. Diagnostics are in DataFrame.attrs.
    """
    source = Path(path)
    raw = source.read_bytes()
    try:
        content = raw.decode("utf-8-sig")
        encoding = "utf-8-sig"
    except UnicodeDecodeError:
        content = raw.decode("cp1251")
        encoding = "cp1251"
    rows, current = [], None
    diagnostics = {"encoding": encoding, "headers": 0, "excluded_messages": 0,
                   "ignored_lines": 0, "chronology_inversions": 0}
    previous_author, turn_id = None, 0

    def finish():
        if current is None:
            return
        own, quotes = [], []
        for line in current.pop("_lines"):
            if line.lstrip().startswith(">"):
                quotes.append(line)
            elif _normalized_marker(line) in MEDIA_MARKERS | SERVICE_MARKERS:
                diagnostics["ignored_lines"] += 1
            else:
                own.append(line)
        text = "\n".join(own).strip("\r\n")
        if not text.strip():
            diagnostics["excluded_messages"] += 1
            return
        current["text"] = text
        current["quoted_text"] = "\n".join(quotes)
        rows.append(current.copy())

    for line_number, line in enumerate(content.splitlines(), 1):
        match = HEADER.match(line)
        if match:
            finish()
            stamp, attribution, _, first_line = match.groups()
            try:
                moment = datetime.strptime(stamp, "%d.%m.%Y %H:%M:%S" if stamp.count(":") == 2 else "%d.%m.%Y %H:%M")
            except ValueError as exc:
                raise ValueError(f"Некорректная дата в строке {line_number}: {stamp}") from exc
            reply = re.match(r"^(.*?)\s+(?:в ответ|in reply to)\s+(.+)$", attribution, re.IGNORECASE)
            author = (reply.group(1) if reply else attribution).strip()
            target = reply.group(2).strip() if reply else ""
            if not author or (reply and not target):
                raise ValueError(f"Не указан автор или адресат ответа в строке {line_number}")
            if author != previous_author:
                turn_id += 1
            previous_author = author
            diagnostics["headers"] += 1
            current = {"message_id": diagnostics["headers"], "datetime": moment,
                       "author": author, "is_reply": bool(reply),
                       "reply_to_author": target if reply else None,
                       "source_file": source.name, "_turn_id": turn_id,
                       "_lines": [first_line]}
        elif DATED_LINE.match(line):
            # Timestamped records without 'author:' are system events and
            # must not become a continuation of the preceding message.
            finish()
            current = None
            diagnostics["ignored_lines"] += 1
        elif line.strip().casefold() in SERVICE_MARKERS:
            diagnostics["ignored_lines"] += 1
        elif current is not None:
            current["_lines"].append(line)
        elif line.strip():
            diagnostics["ignored_lines"] += 1
    finish()
    frame = pd.DataFrame(rows, columns=COLUMNS)
    frame["datetime"] = pd.to_datetime(frame["datetime"])
    diagnostics["chronology_inversions"] = int((frame["datetime"].diff().dt.total_seconds() < 0).sum())
    frame.attrs["diagnostics"] = diagnostics
    return frame


def _normalized_marker(line: str) -> str:
    """Normalize harmless whitespace inside exact bracketed media markers."""
    value = line.strip().casefold()
    match = re.fullmatch(r"\[\s*(.*?)\s*\]", value)
    return f"[{match.group(1)}]" if match else value

