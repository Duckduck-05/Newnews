"""Stage 4 — Deliver (§8 của brief): format Telegram + gửi qua Bot API.

Tôn trọng DRY_RUN: true -> in console, không gọi Telegram API thật.
Nhãn 🟢🟡🔴 giữ nguyên trong text, không bị format/escape mất.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Optional

import requests

logger = logging.getLogger(__name__)

TELEGRAM_API_URL = "https://api.telegram.org/bot{token}/sendMessage"
TELEGRAM_MAX_LEN = 4096
DEFAULT_TIMEOUT_S = 20

# Thứ tự thứ trong tuần tiếng Việt cho header.
WEEKDAY_VI = [
    "Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật",
]


def format_header(now: Optional[datetime] = None) -> str:
    now = now or datetime.now()
    weekday = WEEKDAY_VI[now.weekday()]
    return f"📰 Morning Intel — {now.strftime('%d/%m/%Y')} ({weekday})"


def build_message(digest_text: str, now: Optional[datetime] = None) -> str:
    header = format_header(now)
    return f"{header}\n\n{digest_text.strip()}"


def split_message(text: str, max_len: int = TELEGRAM_MAX_LEN) -> list[str]:
    """Tách message dài thành nhiều phần, cố gắng cắt theo ranh giới dòng để
    không cắt giữa 1 câu/nhãn confidence."""
    if len(text) <= max_len:
        return [text]

    chunks: list[str] = []
    remaining = text
    while len(remaining) > max_len:
        cut_at = remaining.rfind("\n", 0, max_len)
        if cut_at <= 0:
            cut_at = max_len
        chunks.append(remaining[:cut_at].rstrip())
        remaining = remaining[cut_at:].lstrip("\n")
    if remaining:
        chunks.append(remaining)
    return chunks


def send_telegram_message(token: str, chat_id: str, text: str) -> bool:
    url = TELEGRAM_API_URL.format(token=token)
    try:
        resp = requests.post(
            url,
            json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"},
            timeout=DEFAULT_TIMEOUT_S,
        )
        if resp.status_code != 200:
            logger.warning(
                "deliver.py: Telegram trả status %s: %s", resp.status_code, resp.text
            )
            return False
        return True
    except requests.RequestException as exc:
        logger.warning("deliver.py: lỗi gọi Telegram API: %s", exc)
        return False


def deliver(digest_text: str, dry_run: bool = True, now: Optional[datetime] = None) -> bool:
    """Stage 4 đầy đủ: build message, tách nếu quá dài, gửi (hoặc in console
    nếu DRY_RUN). Trả True nếu mọi phần gửi thành công (hoặc dry_run)."""
    full_message = build_message(digest_text, now=now)
    chunks = split_message(full_message)

    if dry_run:
        print("=" * 70)
        print("DRY_RUN=true — KHÔNG gọi Telegram API thật. Nội dung sẽ gửi:")
        print("=" * 70)
        for i, chunk in enumerate(chunks, start=1):
            if len(chunks) > 1:
                print(f"\n--- Phần {i}/{len(chunks)} ---")
            print(chunk)
        return True

    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        logger.warning(
            "deliver.py: thiếu TELEGRAM_BOT_TOKEN hoặc TELEGRAM_CHAT_ID trong "
            "env -> không gửi được, in ra console thay thế (không crash)."
        )
        for chunk in chunks:
            print(chunk)
        return False

    all_ok = True
    for chunk in chunks:
        ok = send_telegram_message(token, chat_id, chunk)
        all_ok = all_ok and ok

    return all_ok
