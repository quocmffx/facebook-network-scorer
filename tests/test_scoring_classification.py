"""
Tests for the ScoringEngine classification logic.
"""

from fb_network_scorer.config import ScoringConfig
from fb_network_scorer.scorer import ScoringEngine
from fb_network_scorer.models import FriendRecord, FriendSignals


def test_classify_keep():
    engine = ScoringEngine(ScoringConfig())
    # Mock a friend signal
    sig = FriendSignals(name="Alice", name_normalized="alice", is_current_friend=True)
    # Give it a high score
    assert engine._classify(composite=50.0, confidence=0.8, sig=sig) == "keep"

    # Give it a recent bidirectional DM
    sig.msg_sent_count = 1
    sig.msg_received_count = 1
    sig.msg_latest_ts = 2000000000  # Far in the future, definitely recent
    assert engine._classify(composite=0.0, confidence=0.0, sig=sig) == "keep"


def test_classify_review():
    engine = ScoringEngine(ScoringConfig())
    sig = FriendSignals(name="Bob", name_normalized="bob", is_current_friend=True)
    
    # Moderate score
    assert engine._classify(composite=15.0, confidence=0.5, sig=sig) == "review"

    # Old bidirectional DM
    sig.msg_sent_count = 1
    sig.msg_received_count = 1
    sig.msg_latest_ts = 100000  # Very old, not recent
    assert engine._classify(composite=0.0, confidence=0.0, sig=sig) == "review"

    # Low confidence but has real person signal (comment)
    sig2 = FriendSignals(name="Charlie", name_normalized="charlie", is_current_friend=True)
    sig2.comment_count = 1
    assert engine._classify(composite=0.0, confidence=0.1, sig=sig2) == "review"


def test_classify_stale():
    engine = ScoringEngine(ScoringConfig())
    sig = FriendSignals(name="Dave", name_normalized="dave", is_current_friend=True)
    
    # No DMs, no comments, only reactions -> stale
    sig.reaction_count = 5
    assert engine._classify(composite=5.0, confidence=0.5, sig=sig) == "stale_connections"


def test_classify_unknown():
    engine = ScoringEngine(ScoringConfig())
    sig = FriendSignals(name="Eve", name_normalized="eve", is_current_friend=True)
    
    # Zero signals, zero confidence
    assert engine._classify(composite=0.0, confidence=0.0, sig=sig) == "unknown_no_signal"


def test_classify_non_friend():
    engine = ScoringEngine(ScoringConfig())
    sig = FriendSignals(name="Page", name_normalized="page", is_current_friend=False)
    
    # Should always return non_friend if not a current friend
    assert engine._classify(composite=100.0, confidence=1.0, sig=sig) == "non_friend"
