"""
Data models for the Facebook Network Scorer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class FriendRecord:
    """A Facebook friend with their add timestamp."""
    name: str
    added_timestamp: int  # Unix epoch


@dataclass
class MessageThread:
    """A parsed message thread between participants."""
    participants: list[str]
    messages: list[dict[str, Any]]
    thread_path: str = ""


@dataclass
class CommentRecord:
    """A parsed comment interaction."""
    timestamp: int
    author: str
    comment_text: str
    mentioned_name: str  # Name extracted from title "... phản hồi bình luận của X"
    title: str


@dataclass
class ReactionRecord:
    """A parsed reaction interaction."""
    timestamp: int
    reaction_type: str
    target_name: str  # Who the reaction was on (author/page)
    target_url: str


@dataclass
class FriendSignals:
    """Aggregated interaction signals for a single friend."""

    name: str
    name_normalized: str
    added_timestamp: int = 0
    is_current_friend: bool = False  # True only if in your_friends.json

    # Message signals
    msg_sent_count: int = 0
    msg_received_count: int = 0
    msg_timestamps: list[int] = field(default_factory=list)
    msg_latest_ts: int = 0

    # Comment signals
    comment_count: int = 0
    comment_real_count: int = 0  # comments with substantial text
    comment_short_count: int = 0
    comment_timestamps: list[int] = field(default_factory=list)
    comment_latest_ts: int = 0

    # Reaction signals
    reaction_count: int = 0
    reaction_timestamps: list[int] = field(default_factory=list)
    reaction_latest_ts: int = 0

    def total_signals(self) -> int:
        return self.msg_sent_count + self.msg_received_count + self.comment_count + self.reaction_count

    def latest_interaction_ts(self) -> int:
        return max(self.msg_latest_ts, self.comment_latest_ts, self.reaction_latest_ts, 0)

    def has_bidirectional_dm(self) -> bool:
        """True if both sent and received at least 1 message."""
        return self.msg_sent_count > 0 and self.msg_received_count > 0

    def has_recent_bidirectional_dm(self, cutoff_ts: int) -> bool:
        """True if bidirectional AND latest message is within cutoff."""
        return self.has_bidirectional_dm() and self.msg_latest_ts >= cutoff_ts

    def has_dm(self) -> bool:
        return (self.msg_sent_count + self.msg_received_count) > 0

    def has_any_real_person_signal(self) -> bool:
        """True if there's any signal that indicates a real person interaction (not just page likes)."""
        return self.has_dm() or self.comment_count > 0

    def source_channels(self) -> str:
        """Comma-separated list of active signal channels."""
        channels = []
        if self.msg_sent_count + self.msg_received_count > 0:
            channels.append("message")
        if self.comment_count > 0:
            channels.append("comment")
        if self.reaction_count > 0:
            channels.append("reaction")
        return ",".join(channels) if channels else "none"


@dataclass
class FriendScore:
    """Final scored output for a single friend."""
    facebook_name: str
    is_current_friend: bool = False
    interaction_score: float = 0.0
    message_score: float = 0.0
    reaction_score: float = 0.0
    comment_score: float = 0.0
    recency_score: float = 0.0
    context_score: float = 0.0
    last_interaction_at: str = ""
    classification: str = "unknown_no_signal"
    confidence: float = 0.0
    source_channels: str = "none"
    signal_count: int = 0
