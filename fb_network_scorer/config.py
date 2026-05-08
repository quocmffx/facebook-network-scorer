"""
Scoring configuration - all tunable parameters in one place.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ScoringConfig:
    """Immutable scoring configuration."""

    # --- Time Decay ---
    # Lambda for exponential decay: weight = exp(-lambda * days)
    # Half-life ~ 180 days => lambda = ln(2) / 180 ~ 0.00385
    decay_lambda: float = 0.00385

    # --- Channel Weights (raw signal importance) ---
    weight_message: float = 5.0
    weight_comment: float = 3.0
    weight_reaction: float = 1.0

    # --- Message Scoring ---
    # Bidirectional conversation multiplier
    msg_bidirectional_bonus: float = 2.0
    # Penalty for one-sided spam
    msg_one_sided_penalty: float = 0.3
    # Recent conversation boost (messages within last N days)
    msg_recency_boost_days: int = 90
    msg_recency_boost_factor: float = 1.5

    # --- Comment Scoring ---
    # Minimum comment length to count as "real" interaction
    comment_real_min_length: int = 10
    # Weight for short/tag comments vs real comments
    comment_short_weight: float = 0.3
    comment_real_weight: float = 1.0

    # --- Reaction Scoring ---
    # Base reaction weight (weak signal)
    reaction_base_weight: float = 0.2
    # Repeated reactions trust boost (log scale)
    reaction_repeat_boost_factor: float = 0.5

    # --- Context Drift ---
    # Days without any signal to start context decay
    context_drift_start_days: int = 365
    # Maximum drift penalty (0 = full penalty, 1 = no penalty)
    context_drift_floor: float = 0.1

    # --- Classification Thresholds ---
    # Composite score thresholds (0-100 normalized)
    threshold_keep: float = 40.0
    threshold_review: float = 10.0
    threshold_stale: float = 5.0
    # Below threshold_stale => unknown_no_signal (if confidence < min_confidence)

    # --- Confidence ---
    # Minimum data points needed for high confidence
    min_signals_for_high_confidence: int = 5
    min_confidence_to_classify: float = 0.3

    # --- Fuzzy Matching ---
    # Minimum score for fuzzy name matching (0-100)
    fuzzy_match_threshold: int = 80

    # --- Owner name (auto-detected from export) ---
    owner_name: str = ""


DEFAULT_CONFIG = ScoringConfig()
