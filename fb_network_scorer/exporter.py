"""
CSV export module.
Writes scored results to structured CSV files.

Output structure:
  Full graph:
    fb_friend_score.csv          - ALL contacts (friends + non-friends)

  Friend-only cleanup files:
    current_friends_scored.csv   - All current friends with scores
    current_friends_keep.csv     - Friends: keep
    current_friends_review.csv   - Friends: review
    current_friends_stale.csv    - Friends: stale_connections
    unknown_no_signal.csv        - Friends: zero signal

  Non-friend contacts:
    non_friend_contacts.csv      - Pages, groups, strangers
"""

from __future__ import annotations

import csv
import logging
from pathlib import Path

from .models import FriendScore

logger = logging.getLogger(__name__)

FIELDNAMES = [
    "facebook_name",
    "is_current_friend",
    "interaction_score",
    "message_score",
    "reaction_score",
    "comment_score",
    "recency_score",
    "context_score",
    "last_interaction_at",
    "classification",
    "confidence",
    "source_channels",
    "signal_count",
]


def _write_csv(path: Path, rows: list[FriendScore]) -> None:
    """Write a list of FriendScore to CSV."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in rows:
            writer.writerow({
                "facebook_name": row.facebook_name,
                "is_current_friend": row.is_current_friend,
                "interaction_score": row.interaction_score,
                "message_score": row.message_score,
                "reaction_score": row.reaction_score,
                "comment_score": row.comment_score,
                "recency_score": row.recency_score,
                "context_score": row.context_score,
                "last_interaction_at": row.last_interaction_at,
                "classification": row.classification,
                "confidence": row.confidence,
                "source_channels": row.source_channels,
                "signal_count": row.signal_count,
            })
    logger.info("Wrote %d rows to %s", len(rows), path.name)


def export_all(scores: list[FriendScore], output_dir: Path) -> None:
    """
    Export all scored relationships into separated CSV files.

    Input: List of FriendScore objects and output directory path.
    Output: None. Writes multiple CSV files to the output directory.
    Failure mode: Fails if the output directory is not writable.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # --- Full graph (all contacts) ---
    _write_csv(output_dir / "fb_friend_score.csv", scores)

    # --- Split by friend status ---
    friends = [s for s in scores if s.is_current_friend]
    non_friends = [s for s in scores if not s.is_current_friend]

    # --- Friend-only files ---
    _write_csv(output_dir / "current_friends_scored.csv", friends)

    keep = [s for s in friends if s.classification == "keep"]
    review = [s for s in friends if s.classification == "review"]
    stale = [s for s in friends if s.classification == "stale_connections"]
    unknown = [s for s in friends if s.classification == "unknown_no_signal"]

    _write_csv(output_dir / "current_friends_keep.csv", keep)
    _write_csv(output_dir / "current_friends_review.csv", review)
    _write_csv(output_dir / "current_friends_stale.csv", stale)
    _write_csv(output_dir / "unknown_no_signal.csv", unknown)

    # --- Non-friend contacts ---
    _write_csv(output_dir / "non_friend_contacts.csv", non_friends)

    # Summary
    print(f"\n--- Classification Summary ---")
    print(f"  Current friends:     {len(friends)}")
    print(f"    keep:              {len(keep)}")
    print(f"    review:            {len(review)}")
    print(f"    stale:             {len(stale)}")
    print(f"    unknown_no_signal: {len(unknown)}")
    print(f"  Non-friend contacts: {len(non_friends)}")
    print(f"  TOTAL scored:        {len(scores)}")
    print(f"\nOutput directory: {output_dir.resolve()}")

    from .dashboard import export_public_safe_dashboard
    dashboard_path = export_public_safe_dashboard(scores, output_dir)
    print(f"Public-safe dashboard: {dashboard_path.resolve()}")
