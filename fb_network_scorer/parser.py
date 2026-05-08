"""
Facebook export JSON parser.

Handles Meta's "Download Your Information" format:
- Double-encoded UTF-8 (mojibake) for Vietnamese text
- Variable schema across exports
- Graceful degradation on missing files/fields
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Generator

logger = logging.getLogger(__name__)


def fix_facebook_encoding(text: str) -> str:
    """
    Fix Facebook's double-encoded UTF-8 mojibake.

    Facebook exports encode Vietnamese as UTF-8 bytes, then re-encodes
    each byte as latin-1 escape sequences in JSON. This results in
    strings like "Ho\\u00c3\\u00a0ng" instead of "Hoàng".

    Strategy: encode as latin-1 (iso-8859-1), decode as UTF-8.
    """
    if not text:
        return text
    try:
        return text.encode("latin-1").decode("utf-8")
    except (UnicodeDecodeError, UnicodeEncodeError):
        return text


def safe_load_json(path: Path) -> Any:
    """Load JSON with graceful error handling."""
    if not path.exists():
        logger.warning("File not found: %s", path)
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        logger.error("Failed to parse %s: %s", path, e)
        return None


def find_json_files(directory: Path, pattern: str = "*.json") -> list[Path]:
    """Find all JSON files in a directory, sorted by name."""
    if not directory.exists():
        logger.warning("Directory not found: %s", directory)
        return []
    return sorted(directory.glob(pattern))


# ---- Data structures ----

from .models import CommentRecord, FriendRecord, MessageThread, ReactionRecord

# ---- Parsers ----


def parse_friends(export_root: Path) -> list[FriendRecord]:
    """
    Parse the user's friend list to establish the baseline network.

    Input: Path to the Facebook export root directory.
    Output: List of FriendRecord objects.
    Failure mode: Returns an empty list if the friends JSON file is missing or invalid.
    """
    path = export_root / "connections" / "friends" / "your_friends.json"
    data = safe_load_json(path)
    if not data:
        return []

    friends: list[FriendRecord] = []
    # Schema: {"friends_v2": [{"name": "...", "timestamp": 123}]}
    raw_list = data.get("friends_v2", [])
    for item in raw_list:
        name = fix_facebook_encoding(item.get("name", ""))
        ts = item.get("timestamp", 0)
        if name:
            friends.append(FriendRecord(name=name, added_timestamp=ts))

    logger.info("Parsed %d friends", len(friends))
    return friends


def parse_messages(export_root: Path) -> Generator[MessageThread, None, None]:
    """
    Parse all direct message threads to measure bidirectional interaction.

    Input: Path to the Facebook export root directory.
    Output: Generator yielding MessageThread objects one by one (memory efficient).
    Failure mode: Yields nothing if the messages directory is missing. Skips unreadable files.
    """
    inbox_dir = export_root / "your_facebook_activity" / "messages" / "inbox"
    if not inbox_dir.exists():
        logger.warning("Inbox directory not found: %s", inbox_dir)
        return

    thread_dirs = sorted(d for d in inbox_dir.iterdir() if d.is_dir())
    logger.info("Found %d message thread directories", len(thread_dirs))

    for thread_dir in thread_dirs:
        msg_files = find_json_files(thread_dir, "message_*.json")
        if not msg_files:
            continue

        all_messages: list[dict[str, Any]] = []
        participants: list[str] = []

        for msg_file in msg_files:
            data = safe_load_json(msg_file)
            if not data:
                continue

            # Extract participants from first file
            if not participants:
                raw_participants = data.get("participants", [])
                participants = [
                    fix_facebook_encoding(p.get("name", ""))
                    for p in raw_participants
                    if p.get("name")
                ]

            raw_messages = data.get("messages", [])
            for msg in raw_messages:
                parsed_msg = {
                    "sender": fix_facebook_encoding(msg.get("sender_name", "")),
                    "timestamp_ms": msg.get("timestamp_ms", 0),
                    "content": fix_facebook_encoding(msg.get("content", "")),
                    "has_photos": bool(msg.get("photos")),
                    "has_share": bool(msg.get("share")),
                    "is_unsent": msg.get("is_unsent", False),
                    "call_duration": msg.get("call_duration"),
                }
                all_messages.append(parsed_msg)

        if participants and all_messages:
            yield MessageThread(
                participants=participants,
                messages=all_messages,
                thread_path=thread_dir.name,
            )


def _extract_name_from_title(title: str) -> str:
    """
    Extract the target person name from a comment title.

    Patterns (after encoding fix):
    - "X đã phản hồi bình luận của Y." => Y
    - "X đã bình luận về bài viết của Y." => Y
    - "X đã trả lời bình luận của chính anh ấy." => "" (self)
    """
    if not title:
        return ""

    title = fix_facebook_encoding(title)

    # Pattern: "... của X." - extract X
    markers = [
        "phản hồi bình luận của ",
        "bình luận về bài viết của ",
        "bình luận về ảnh của ",
        "bình luận về thước phim của ",
        "bình luận về tiểu sử của ",
        "trả lời bình luận của ",
    ]

    for marker in markers:
        idx = title.find(marker)
        if idx != -1:
            name = title[idx + len(marker):].rstrip(".")
            # Skip self-references
            if name in ("chính mình", "chính anh ấy", "chính cô ấy"):
                return ""
            return name

    return ""


def _extract_mentioned_name_from_comment(comment_text: str) -> str:
    """
    Extract tagged name from comment text.

    Facebook comments often start with a tagged name like:
    "Hoàng Chất thằng loz, t báo CA bắt m"
    The tagged name is the first part before the actual comment.

    This is a heuristic - we extract the first word(s) that look like
    a Vietnamese name (capitalized words at the start).
    """
    if not comment_text:
        return ""
    # This is too unreliable for scoring purposes
    # We rely on title parsing instead
    return ""


def parse_comments(export_root: Path) -> list[CommentRecord]:
    """
    Parse comments on posts to measure public interaction signals.

    Input: Path to the Facebook export root directory.
    Output: List of CommentRecord objects.
    Failure mode: Returns an empty list if the comments file is missing or unreadable.
    """
    comments_dir = export_root / "your_facebook_activity" / "comments_and_reactions"
    path = comments_dir / "comments.json"
    data = safe_load_json(path)
    if not data:
        return []

    records: list[CommentRecord] = []
    raw_list = data.get("comments_v2", [])

    for item in raw_list:
        ts = item.get("timestamp", 0)
        title = item.get("title", "")

        # Extract comment text and author
        comment_text = ""
        author = ""
        data_list = item.get("data", [])
        for d in data_list:
            comment_obj = d.get("comment", {})
            if comment_obj:
                comment_text = fix_facebook_encoding(comment_obj.get("comment", ""))
                author = fix_facebook_encoding(comment_obj.get("author", ""))
                break

        mentioned_name = _extract_name_from_title(title)

        records.append(CommentRecord(
            timestamp=ts,
            author=author,
            comment_text=comment_text,
            mentioned_name=mentioned_name,
            title=fix_facebook_encoding(title),
        ))

    logger.info("Parsed %d comments", len(records))
    return records


def parse_reactions(export_root: Path) -> list[ReactionRecord]:
    """
    Parse reactions (likes, loves, etc.) to capture low-friction engagement.

    Input: Path to the Facebook export root directory.
    Output: List of ReactionRecord objects.
    Failure mode: Returns an empty list if no reaction files are found or if they are malformed.
    """
    reactions_dir = export_root / "your_facebook_activity" / "comments_and_reactions"
    records: list[ReactionRecord] = []

    reaction_files = find_json_files(reactions_dir, "likes_and_reactions*.json")
    if not reaction_files:
        logger.warning("No reaction files found in %s", reactions_dir)
        return []

    for rfile in reaction_files:
        data = safe_load_json(rfile)
        if not data:
            continue

        # Schema: top-level array
        raw_list = data if isinstance(data, list) else []

        for item in raw_list:
            ts = item.get("timestamp", 0)
            label_values = item.get("label_values", [])

            reaction_type = ""
            target_url = ""
            target_name = ""

            for lv in label_values:
                label = fix_facebook_encoding(lv.get("label", ""))
                value = fix_facebook_encoding(lv.get("value", ""))

                if label in ("Cảm xúc", "Reaction"):
                    reaction_type = value
                elif label == "URL":
                    target_url = value
                elif label in ("Tên", "Name"):
                    target_name = value

                # Check nested dict for author/group info
                title_field = fix_facebook_encoding(lv.get("title", ""))
                if title_field in ("Tác giả", "Author"):
                    dict_items = lv.get("dict", [])
                    for di in dict_items:
                        inner_dicts = di.get("dict", [])
                        for inner in inner_dicts:
                            inner_label = fix_facebook_encoding(inner.get("label", ""))
                            if inner_label in ("Tên", "Name"):
                                target_name = fix_facebook_encoding(inner.get("value", ""))

                # Also check Chủ sở hữu for comment reactions
                if title_field in ("Chủ sở hữu", "Owner"):
                    dict_items = lv.get("dict", [])
                    for di in dict_items:
                        inner_dicts = di.get("dict", [])
                        for inner in inner_dicts:
                            inner_label = fix_facebook_encoding(inner.get("label", ""))
                            if inner_label in ("Tên", "Name"):
                                if not target_name:
                                    target_name = fix_facebook_encoding(inner.get("value", ""))

            if reaction_type:
                records.append(ReactionRecord(
                    timestamp=ts,
                    reaction_type=reaction_type,
                    target_name=target_name,
                    target_url=target_url,
                ))

    logger.info("Parsed %d reactions", len(records))
    return records


def detect_owner_name(export_root: Path) -> str:
    """
    Attempt to auto-detect the profile owner's name to filter self-interactions.

    Input: Path to the Facebook export root directory.
    Output: The detected name as a string, or an empty string if detection fails.
    Failure mode: Returns an empty string if profile information cannot be parsed.
    """
    # Try profile info first
    profile_path = export_root / "personal_information" / "profile_information" / "profile_information.json"
    data = safe_load_json(profile_path)
    if data:
        # Schema varies, try common paths
        profile = data.get("profile_v2", data.get("profile", {}))
        if isinstance(profile, dict):
            name = profile.get("name", {})
            if isinstance(name, dict):
                full = name.get("full_name", "")
                if full:
                    return fix_facebook_encoding(full)
            elif isinstance(name, str) and name:
                return fix_facebook_encoding(name)

    # Fallback: check first comment author
    comments_path = export_root / "your_facebook_activity" / "comments_and_reactions" / "comments.json"
    data = safe_load_json(comments_path)
    if data:
        for item in data.get("comments_v2", [])[:10]:
            for d in item.get("data", []):
                author = d.get("comment", {}).get("author", "")
                if author:
                    return fix_facebook_encoding(author)

    return ""
