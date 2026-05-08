"""
Tests for parsing the Facebook JSON export format using the generated fake dataset.
"""

from pathlib import Path
from fb_network_scorer.parser import (
    parse_friends,
    parse_messages,
    parse_comments,
    parse_reactions,
    detect_owner_name,
)


def test_detect_owner_name():
    export_root = Path("examples/sample_export")
    if not export_root.exists():
        return  # Skip if fake data wasn't generated
    name = detect_owner_name(export_root)
    assert name == "Demo User"


def test_parse_friends():
    export_root = Path("examples/sample_export")
    if not export_root.exists():
        return
    friends = parse_friends(export_root)
    assert len(friends) == 2
    names = {f.name for f in friends}
    assert "Alice Nguyen" in names
    assert "Bob Tran" in names


def test_parse_messages():
    export_root = Path("examples/sample_export")
    if not export_root.exists():
        return
    threads = list(parse_messages(export_root))
    assert len(threads) == 1
    thread = threads[0]
    assert "Alice Nguyen" in thread.participants
    assert "Demo User" in thread.participants
    assert len(thread.messages) == 1
    assert thread.messages[0]["sender"] == "Alice Nguyen"
    assert thread.messages[0]["content"] == "Hello"


def test_parse_comments():
    export_root = Path("examples/sample_export")
    if not export_root.exists():
        return
    comments = parse_comments(export_root)
    assert len(comments) == 1
    comment = comments[0]
    assert comment.author == "Charlie Le"
    assert comment.mentioned_name == "Demo User"
    assert comment.comment_text == "Nice photo!"


def test_parse_reactions():
    export_root = Path("examples/sample_export")
    if not export_root.exists():
        return
    reactions = parse_reactions(export_root)
    assert len(reactions) == 1
    reaction = reactions[0]
    assert reaction.reaction_type == "Thích"
    assert reaction.target_name == "Bob Tran"
