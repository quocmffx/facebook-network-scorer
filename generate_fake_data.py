import json
import os
from pathlib import Path

export_root = Path("examples/sample_export")
out_root = Path("examples/sample_output")

export_root.mkdir(parents=True, exist_ok=True)
out_root.mkdir(parents=True, exist_ok=True)

# 1. Create the flat files requested by the user
with open(export_root / "fake_friends.json", "w", encoding="utf-8") as f:
    json.dump({"friends_v2": [{"name": "Alice Nguyen", "timestamp": 1600000000}, {"name": "Bob Tran", "timestamp": 1600000000}]}, f)

with open(export_root / "fake_messages.json", "w", encoding="utf-8") as f:
    json.dump({"messages": [{"sender_name": "Alice Nguyen", "timestamp_ms": 1700000000000, "content": "Hello"}], "participants": [{"name": "Alice Nguyen"}, {"name": "Demo User"}]}, f)

with open(export_root / "fake_reactions.json", "w", encoding="utf-8") as f:
    json.dump([{"timestamp": 1700000000, "label_values": [{"label": "Reaction", "value": "Thích"}, {"label": "Name", "value": "Bob Tran"}]}], f)

with open(export_root / "fake_comments.json", "w", encoding="utf-8") as f:
    json.dump({"comments_v2": [{"timestamp": 1700000000, "title": "Demo User đã bình luận về ảnh của Charlie Le.", "data": [{"comment": {"comment": "Nice photo!", "author": "Demo User"}}]}]}, f)

with open(export_root / "README.md", "w", encoding="utf-8") as f:
    f.write("# Sample Export\nContains fake data for testing.\n")

# 2. ALSO create the expected Meta directory structure so the script actually works without modifying parser.py!
conn_dir = export_root / "connections" / "friends"
conn_dir.mkdir(parents=True, exist_ok=True)
with open(conn_dir / "your_friends.json", "w", encoding="utf-8") as f:
    json.dump({"friends_v2": [{"name": "Alice Nguyen", "timestamp": 1600000000}, {"name": "Bob Tran", "timestamp": 1600000000}]}, f)

msg_dir = export_root / "your_facebook_activity" / "messages" / "inbox" / "alicenguyen_123"
msg_dir.mkdir(parents=True, exist_ok=True)
with open(msg_dir / "message_1.json", "w", encoding="utf-8") as f:
    json.dump({"messages": [{"sender_name": "Alice Nguyen", "timestamp_ms": 1700000000000, "content": "Hello"}], "participants": [{"name": "Alice Nguyen"}, {"name": "Demo User"}]}, f)

react_dir = export_root / "your_facebook_activity" / "comments_and_reactions"
react_dir.mkdir(parents=True, exist_ok=True)
with open(react_dir / "likes_and_reactions.json", "w", encoding="utf-8") as f:
    json.dump([{"timestamp": 1700000000, "label_values": [{"label": "Reaction", "value": "Thích"}, {"title": "Tác giả", "dict": [{"dict": [{"label": "Tên", "value": "Bob Tran"}]}]}]}], f)

with open(react_dir / "comments.json", "w", encoding="utf-8") as f:
    json.dump({"comments_v2": [{"timestamp": 1700000000, "title": "Charlie Le đã bình luận về ảnh của Demo User.", "data": [{"comment": {"comment": "Nice photo!", "author": "Charlie Le"}}]}]}, f)

# 3. Add personal info so owner name is detected as Demo User
prof_dir = export_root / "personal_information" / "profile_information"
prof_dir.mkdir(parents=True, exist_ok=True)
with open(prof_dir / "profile_information.json", "w", encoding="utf-8") as f:
    json.dump({"profile_v2": {"name": {"full_name": "Demo User"}}}, f)

print("Created examples with fake data.")
