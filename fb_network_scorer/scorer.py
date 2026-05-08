"""
Scoring engine - computes per-friend interaction scores.

Scoring pipeline:
1. Aggregate signals per friend (messages, comments, reactions)
2. Apply time decay to each signal
3. Compute channel-specific sub-scores
4. Compute context drift
5. Classify connections
6. Assign confidence levels
"""

from __future__ import annotations

import logging
import math
import unicodedata
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from rapidfuzz import fuzz, process

from .config import ScoringConfig
from .parser import (
    CommentRecord,
    FriendRecord,
    MessageThread,
    ReactionRecord,
)

logger = logging.getLogger(__name__)

# Current time reference
NOW_TS = int(datetime.now(timezone.utc).timestamp())
SECONDS_PER_DAY = 86400


def normalize_name(name: str) -> str:
    """
    Normalize a Vietnamese name for matching.
    - NFC normalization
    - Lowercase
    - Strip extra whitespace
    """
    if not name:
        return ""
    name = unicodedata.normalize("NFC", name)
    name = " ".join(name.lower().split())
    return name


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


class ScoringEngine:
    """Computes friend scores from parsed signals."""

    def __init__(self, config: ScoringConfig):
        self.config = config
        self._signals: dict[str, FriendSignals] = {}
        self._name_index: dict[str, str] = {}  # normalized -> original
        # Canonical friend set (normalized names from your_friends.json)
        self._friend_norms: set[str] = set()
        self._friend_names: list[str] = []  # original names for fuzzy matching

    def _get_or_create(self, name: str) -> FriendSignals:
        """Get existing signals or create new entry."""
        norm = normalize_name(name)
        if norm in self._signals:
            return self._signals[norm]

        sig = FriendSignals(name=name, name_normalized=norm)
        self._signals[norm] = sig
        self._name_index[norm] = name
        return sig

    def _is_canonical_friend(self, name: str) -> bool:
        """Check if a name matches a canonical friend (exact normalized match)."""
        return normalize_name(name) in self._friend_norms

    def _fuzzy_match_friend(self, name: str) -> str | None:
        """
        Try to fuzzy-match a name against the canonical friend list.
        Returns the matched friend name or None.
        """
        if not name or not self._friend_names:
            return None

        norm = normalize_name(name)
        # Exact match first
        if norm in self._friend_norms:
            return self._name_index.get(norm, name)

        result = process.extractOne(
            norm,
            list(self._friend_norms),
            scorer=fuzz.ratio,
            score_cutoff=self.config.fuzzy_match_threshold,
        )

        if result:
            matched_norm, score, idx = result
            return self._name_index.get(matched_norm, name)
        return None

    def ingest_friends(self, friends: list[FriendRecord]) -> None:
        """Register all friends as canonical friend set."""
        for f in friends:
            sig = self._get_or_create(f.name)
            sig.added_timestamp = f.added_timestamp
            sig.is_current_friend = True
            norm = normalize_name(f.name)
            self._friend_norms.add(norm)
            self._friend_names.append(f.name)
        logger.info("Ingested %d canonical friends", len(friends))

    def ingest_messages(self, thread: MessageThread) -> None:
        """
        Ingest a single message thread.
        Only processes DM threads (2 participants).
        """
        owner = self.config.owner_name
        if not owner:
            return

        # Skip group chats for scoring (noise)
        if len(thread.participants) != 2:
            return

        # Identify the friend in this thread
        owner_norm = normalize_name(owner)
        friend_name = ""
        for p in thread.participants:
            if normalize_name(p) != owner_norm:
                friend_name = p
                break

        if not friend_name:
            return

        sig = self._get_or_create(friend_name)

        for msg in thread.messages:
            if msg.get("is_unsent"):
                continue

            ts_ms = msg.get("timestamp_ms", 0)
            ts = ts_ms // 1000 if ts_ms > 1_000_000_000_000 else ts_ms
            sender = msg.get("sender")

            if normalize_name(sender) == owner_norm:
                sig.msg_sent_count += 1
            else:
                sig.msg_received_count += 1

            sig.msg_timestamps.append(ts)
            if ts > sig.msg_latest_ts:
                sig.msg_latest_ts = ts

    def ingest_comments(self, comments: list[CommentRecord]) -> None:
        """Ingest parsed comments and attribute to friends."""
        owner = self.config.owner_name
        owner_norm = normalize_name(owner) if owner else ""

        for c in comments:
            target = c.mentioned_name
            if not target:
                continue
            if normalize_name(target) == owner_norm:
                continue

            sig = self._get_or_create(target)
            sig.comment_count += 1
            sig.comment_timestamps.append(c.timestamp)

            if len(c.comment_text) >= self.config.comment_real_min_length:
                sig.comment_real_count += 1
            else:
                sig.comment_short_count += 1

            if c.timestamp > sig.comment_latest_ts:
                sig.comment_latest_ts = c.timestamp

    def ingest_reactions(self, reactions: list[ReactionRecord]) -> None:
        """Ingest parsed reactions and attribute to friends."""
        for r in reactions:
            target = r.target_name
            if not target:
                continue

            sig = self._get_or_create(target)
            sig.reaction_count += 1
            sig.reaction_timestamps.append(r.timestamp)

            if r.timestamp > sig.reaction_latest_ts:
                sig.reaction_latest_ts = r.timestamp

    def _time_decay(self, timestamp: int) -> float:
        """Compute time decay weight for a given timestamp."""
        if timestamp <= 0:
            return 0.0
        days_ago = max(0, (NOW_TS - timestamp)) / SECONDS_PER_DAY
        return math.exp(-self.config.decay_lambda * days_ago)

    def _compute_message_score(self, sig: FriendSignals) -> float:
        """
        Compute message score with:
        - Time-decayed message count
        - Bidirectional bonus
        - One-sided penalty
        - Recent conversation boost
        """
        cfg = self.config
        if not sig.msg_timestamps:
            return 0.0

        # Time-decayed message value
        decayed_sum = sum(self._time_decay(ts) for ts in sig.msg_timestamps)

        # Bidirectionality check
        total = sig.msg_sent_count + sig.msg_received_count
        if total == 0:
            return 0.0

        sent_ratio = sig.msg_sent_count / total
        recv_ratio = sig.msg_received_count / total
        balance = min(sent_ratio, recv_ratio) / max(sent_ratio, recv_ratio) if max(sent_ratio, recv_ratio) > 0 else 0

        if balance > 0.2:
            # Good bidirectional conversation
            multiplier = cfg.msg_bidirectional_bonus
        elif min(sig.msg_sent_count, sig.msg_received_count) == 0:
            # Completely one-sided
            multiplier = cfg.msg_one_sided_penalty
        else:
            # Weak bidirectional
            multiplier = 0.5 + balance

        # Recent conversation boost
        recency_cutoff = NOW_TS - (cfg.msg_recency_boost_days * SECONDS_PER_DAY)
        recent_msgs = sum(1 for ts in sig.msg_timestamps if ts > recency_cutoff)
        recency_mult = 1.0
        if recent_msgs > 0:
            recency_mult = cfg.msg_recency_boost_factor

        return decayed_sum * multiplier * recency_mult * cfg.weight_message

    def _compute_comment_score(self, sig: FriendSignals) -> float:
        """
        Compute comment score with:
        - Real comments weighted higher
        - Short/tag comments weighted lower
        - Time decay applied
        """
        cfg = self.config
        if not sig.comment_timestamps:
            return 0.0

        # Approximate: use counts for weights, timestamps for decay
        real_weight = sig.comment_real_count * cfg.comment_real_weight
        short_weight = sig.comment_short_count * cfg.comment_short_weight
        weighted_count = real_weight + short_weight

        if weighted_count == 0:
            return 0.0

        # Average time decay across all comments
        avg_decay = sum(self._time_decay(ts) for ts in sig.comment_timestamps) / len(sig.comment_timestamps)

        return weighted_count * avg_decay * cfg.weight_comment

    def _compute_reaction_score(self, sig: FriendSignals) -> float:
        """
        Compute reaction score with:
        - Weak base signal
        - Repeated reactions increase trust (log scale)
        - Time decay
        """
        cfg = self.config
        if not sig.reaction_timestamps:
            return 0.0

        # Time-decayed reaction sum
        decayed_sum = sum(self._time_decay(ts) for ts in sig.reaction_timestamps)

        # Repeated reactions trust boost (log scale, diminishing returns)
        repeat_factor = 1.0 + cfg.reaction_repeat_boost_factor * math.log1p(sig.reaction_count)

        return decayed_sum * cfg.reaction_base_weight * repeat_factor * cfg.weight_reaction

    def _compute_recency_score(self, sig: FriendSignals) -> float:
        """
        Compute recency score (0-100) based on days since last interaction.
        """
        latest = sig.latest_interaction_ts()
        if latest <= 0:
            return 0.0

        days_ago = max(0, (NOW_TS - latest)) / SECONDS_PER_DAY

        # Exponential decay with gentler lambda for recency
        # Recent = high, old = low
        score = math.exp(-0.005 * days_ago) * 100
        return max(0.0, score)

    def _compute_context_score(self, sig: FriendSignals) -> float:
        """
        Compute context drift score (0-100).

        High = still relevant context
        Low = historical artifact, context drifted
        """
        cfg = self.config
        latest = sig.latest_interaction_ts()

        if latest <= 0:
            # No interaction data at all
            # Check if they were added recently
            if sig.added_timestamp > 0:
                days_since_add = max(0, (NOW_TS - sig.added_timestamp)) / SECONDS_PER_DAY
                if days_since_add < cfg.context_drift_start_days:
                    return 50.0  # Recently added, benefit of doubt
            return cfg.context_drift_floor * 100

        days_since_last = max(0, (NOW_TS - latest)) / SECONDS_PER_DAY

        if days_since_last < cfg.context_drift_start_days:
            return 100.0  # Still within active window

        # Linear decay after drift starts
        drift_days = days_since_last - cfg.context_drift_start_days
        decay = max(cfg.context_drift_floor, 1.0 - (drift_days / (365 * 3)))  # 3 years to floor
        return decay * 100

    def _compute_confidence(self, sig: FriendSignals) -> float:
        """
        Compute confidence level (0-1).
        Low data = low confidence.
        """
        total = sig.total_signals()
        if total == 0:
            return 0.05  # Near-zero confidence

        # Log scale: 1 signal = ~0.3, 5 = ~0.6, 20+ = ~0.9+
        raw = math.log1p(total) / math.log1p(self.config.min_signals_for_high_confidence * 4)
        return min(1.0, max(0.05, raw))

    def _classify(self, composite: float, confidence: float, sig: FriendSignals) -> str:
        """
        Classify connection based on composite score and confidence.
        Only applies to current friends. Non-friends get 'non_friend'.

        Rules (priority order, friends only):
        1. unknown_no_signal: zero signals + zero confidence
        2. keep: composite >= 40 OR bidirectional DM within 365 days
        3. review: composite >= 10 OR ever had bidirectional DM
                   OR low confidence but any real person signal
        4. stale_connections: composite < 10, no DM, no comment,
                             only old reactions or zero signal
        """
        # Non-friends don't get cleanup classification
        if not sig.is_current_friend:
            return "non_friend"

        cfg = self.config
        recent_cutoff = NOW_TS - (365 * SECONDS_PER_DAY)

        # --- unknown_no_signal: data quality issues ---
        if sig.total_signals() == 0 and confidence < cfg.min_confidence_to_classify:
            return "unknown_no_signal"

        # --- keep: strong active connection ---
        if composite >= cfg.threshold_keep:
            return "keep"
        if sig.has_recent_bidirectional_dm(recent_cutoff):
            return "keep"

        # --- review: has history or ambiguous signal ---
        if composite >= cfg.threshold_review:
            return "review"
        if sig.has_bidirectional_dm():
            return "review"
        if confidence < cfg.min_confidence_to_classify and sig.has_any_real_person_signal():
            return "review"

        # --- stale_connections: no DM, no comment, only reactions or nothing ---
        if not sig.has_dm() and sig.comment_count == 0:
            if sig.reaction_count > 0 or sig.total_signals() == 0:
                return "stale_connections"

        # Fallback: has some signal but weak
        if sig.total_signals() > 0:
            return "stale_connections"

        return "unknown_no_signal"

    def _resolve_friend_flags(self) -> None:
        """
        After all signals are ingested, try to fuzzy-match non-friend
        contacts against the canonical friend list. This catches cases
        where a friend's display name in messages/comments differs
        slightly from their friend list name.
        """
        matched = 0
        for norm, sig in list(self._signals.items()):
            if sig.is_current_friend:
                continue
            # Try fuzzy match
            match = self._fuzzy_match_friend(sig.name)
            if match:
                match_norm = normalize_name(match)
                if match_norm in self._signals and match_norm != norm:
                    # Merge signals into the canonical friend entry
                    target = self._signals[match_norm]
                    target.msg_sent_count += sig.msg_sent_count
                    target.msg_received_count += sig.msg_received_count
                    target.msg_timestamps.extend(sig.msg_timestamps)
                    target.msg_latest_ts = max(target.msg_latest_ts, sig.msg_latest_ts)
                    target.comment_count += sig.comment_count
                    target.comment_real_count += sig.comment_real_count
                    target.comment_short_count += sig.comment_short_count
                    target.comment_timestamps.extend(sig.comment_timestamps)
                    target.comment_latest_ts = max(target.comment_latest_ts, sig.comment_latest_ts)
                    target.reaction_count += sig.reaction_count
                    target.reaction_timestamps.extend(sig.reaction_timestamps)
                    target.reaction_latest_ts = max(target.reaction_latest_ts, sig.reaction_latest_ts)
                    # Remove the duplicate
                    del self._signals[norm]
                    matched += 1
        if matched:
            logger.info("Fuzzy-merged %d contacts into canonical friends", matched)

    def compute_scores(self) -> list[FriendScore]:
        """
        Compute final scores for all tracked friends/contacts.
        Returns sorted list (highest score first).
        """
        # Resolve fuzzy friend matches before scoring
        self._resolve_friend_flags()

        results: list[FriendScore] = []
        friend_count = sum(1 for s in self._signals.values() if s.is_current_friend)
        non_friend_count = sum(1 for s in self._signals.values() if not s.is_current_friend)
        logger.info("Scoring %d current friends + %d non-friend contacts", friend_count, non_friend_count)

        for norm_name, sig in self._signals.items():
            msg_score = self._compute_message_score(sig)
            comment_score = self._compute_comment_score(sig)
            reaction_score = self._compute_reaction_score(sig)
            recency = self._compute_recency_score(sig)
            context = self._compute_context_score(sig)

            # Composite: weighted sum normalized to 0-100
            raw_composite = msg_score + comment_score + reaction_score
            # Apply context as a multiplier
            composite = raw_composite * (context / 100.0)

            confidence = self._compute_confidence(sig)
            classification = self._classify(composite, confidence, sig)

            # Format last interaction
            latest_ts = sig.latest_interaction_ts()
            last_interaction_str = ""
            if latest_ts > 0:
                last_interaction_str = datetime.fromtimestamp(
                    latest_ts, tz=timezone.utc
                ).strftime("%Y-%m-%d")

            results.append(FriendScore(
                facebook_name=sig.name,
                is_current_friend=sig.is_current_friend,
                interaction_score=round(composite, 2),
                message_score=round(msg_score, 2),
                reaction_score=round(reaction_score, 2),
                comment_score=round(comment_score, 2),
                recency_score=round(recency, 2),
                context_score=round(context, 2),
                last_interaction_at=last_interaction_str,
                classification=classification,
                confidence=round(confidence, 2),
                source_channels=sig.source_channels(),
                signal_count=sig.total_signals(),
            ))

        # Sort by interaction_score descending
        results.sort(key=lambda x: x.interaction_score, reverse=True)
        logger.info("Computed scores for %d contacts", len(results))
        return results
