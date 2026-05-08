import pytest
from pathlib import Path
from fb_network_scorer.models import FriendScore
from fb_network_scorer.dashboard import export_public_safe_dashboard

def test_export_public_safe_dashboard(tmp_path: Path):
    scores = [
        FriendScore(facebook_name="Alice", is_current_friend=True, interaction_score=1500, classification="keep", signal_count=50, source_channels="message,comment,reaction"),
        FriendScore(facebook_name="Bob", is_current_friend=True, interaction_score=800, classification="keep", signal_count=20, source_channels="message,reaction"),
        FriendScore(facebook_name="Charlie", is_current_friend=True, interaction_score=15, classification="review", signal_count=2, source_channels="comment"),
        FriendScore(facebook_name="David", is_current_friend=True, interaction_score=8, classification="stale_connections", signal_count=1, source_channels="reaction"),
        FriendScore(facebook_name="Eve", is_current_friend=True, interaction_score=0, classification="unknown_no_signal", signal_count=0, source_channels="none"),
        FriendScore(facebook_name="Stranger", is_current_friend=False, interaction_score=50, classification="unknown_no_signal", signal_count=5, source_channels="comment"),
    ]
    
    dashboard_path = export_public_safe_dashboard(scores, tmp_path)
    
    assert dashboard_path.exists()
    
    content = dashboard_path.read_text(encoding="utf-8")
    
    # Assert specific text exists
    assert "PUBLIC SAFE MODE" in content
    assert "Node_001" in content
    
    # Assert real names are NOT in the dashboard
    assert "Alice" not in content
    assert "Bob" not in content
    assert "Charlie" not in content
    assert "David" not in content
    assert "Eve" not in content
    assert "Stranger" not in content
    
    # Assert no external or tracking resources
    assert "https://" not in content
    assert "cdnjs" not in content
    assert "data-real" not in content

def test_export_public_safe_dashboard_empty(tmp_path: Path):
    scores = []
    dashboard_path = export_public_safe_dashboard(scores, tmp_path)
    
    assert dashboard_path.exists()
    content = dashboard_path.read_text(encoding="utf-8")
    assert "PUBLIC SAFE MODE" in content
