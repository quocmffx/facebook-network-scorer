import logging
from pathlib import Path
from .models import FriendScore

logger = logging.getLogger(__name__)

def format_score(score: float) -> str:
    if score >= 1000:
        return f"{score/1000:.1f}k"
    elif score >= 100:
        return f"{int(round(score))}"
    elif score == int(score):
        return f"{int(score)}"
    else:
        return f"{score:.2f}"

def format_channels(channels: str) -> str:
    mapping = {
        "message": "msg",
        "comment": "cmt",
        "reaction": "rxn"
    }
    parts = [c.strip() for c in channels.split(",") if c.strip() != "none" and c.strip()]
    if not parts:
        return ""
    return ", ".join(mapping.get(c, c) for c in parts)

def export_public_safe_dashboard(scores: list[FriendScore], output_dir: Path) -> Path:
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.error(f"Cannot create output directory {output_dir}: {e}")
        raise

    observed_contacts = len(scores)
    current_friends = [s for s in scores if s.is_current_friend]
    num_current = len(current_friends)
    non_friend_contacts = observed_contacts - num_current

    keep = [s for s in current_friends if s.classification == "keep"]
    review = [s for s in current_friends if s.classification == "review"]
    stale = [s for s in current_friends if s.classification == "stale_connections"]
    unknown = [s for s in current_friends if s.classification == "unknown_no_signal"]

    keep_pct = (len(keep) / num_current * 100) if num_current else 0
    review_pct = (len(review) / num_current * 100) if num_current else 0
    stale_pct = (len(stale) / num_current * 100) if num_current else 0
    unknown_pct = (len(unknown) / num_current * 100) if num_current else 0

    p1 = keep_pct
    p2 = p1 + review_pct
    p3 = p2 + stale_pct

    node_counter = 1
    def get_node():
        nonlocal node_counter
        res = f"Node_{node_counter:03d}"
        node_counter += 1
        return res

    sorted_friends = sorted(current_friends, key=lambda s: s.interaction_score, reverse=True)
    top_10 = sorted_friends[:10]
    
    max_score = top_10[0].interaction_score if top_10 else 1.0
    if max_score <= 0:
        max_score = 1.0

    bar_html = ""
    for s in top_10:
        node_id = get_node()
        width = (s.interaction_score / max_score) * 100 if max_score > 0 else 0
        val = format_score(s.interaction_score)
        bar_html += f'<div class="bar-row"><div class="bar-label">{node_id}</div><div class="bar-track"><div class="bar-fill" style="width: {width:.1f}%;"></div></div><div class="bar-val">{val}</div></div>\n        '

    top_review = sorted(review, key=lambda s: s.interaction_score, reverse=True)[:3]
    review_html = ""
    for s in top_review:
        node_id = get_node()
        val = format_score(s.interaction_score)
        ch = format_channels(s.source_channels)
        review_html += f'<tr class="trow"><td style="color:var(--color-text-primary);">{node_id}</td><td style="text-align:right;color:#BA7517;">{val}</td><td style="text-align:right;color:var(--color-text-secondary);">{s.signal_count}</td><td style="color:var(--color-text-secondary);">{ch}</td></tr>\n          '

    top_stale = sorted(stale, key=lambda s: s.interaction_score, reverse=True)[:5]
    stale_html = ""
    for s in top_stale:
        node_id = get_node()
        val = format_score(s.interaction_score)
        ch = format_channels(s.source_channels)
        stale_html += f'<tr class="trow"><td style="color:var(--color-text-secondary);">{node_id}</td><td style="text-align:right;color:#D85A30;">{val}</td><td style="text-align:right;color:var(--color-text-tertiary);">{s.signal_count}</td><td style="color:var(--color-text-tertiary);">{ch}</td></tr>\n          '

    top_unknown = unknown[:9]
    unknown_html = ""
    for _ in top_unknown:
        node_id = get_node()
        unknown_html += f'<span class="ch-tag">{node_id}</span>\n      '

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Facebook Network Analysis Dashboard</title>
<h2 class="sr-only" style="display:none;">Facebook network analysis dashboard — {num_current} friends phân loại theo interaction score</h2>
<style>
:root {{
  --color-background-primary: #121212;
  --color-background-secondary: #1e1e1e;
  --color-border-primary: #444;
  --color-border-secondary: #333;
  --color-border-tertiary: #2a2a2a;
  --color-text-primary: #eee;
  --color-text-secondary: #aaa;
  --color-text-tertiary: #777;
  --font-mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
  --border-radius-lg: 12px;
  --border-radius-md: 8px;
}}
body {{
  background: #000;
  color: var(--color-text-primary);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  margin: 0;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
}}
.screenshot-wrapper {{
  width: 1200px;
  min-height: 760px;
  height: auto;
  background: var(--color-background-primary);
  padding: 24px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  border: 1px solid var(--color-border-tertiary);
}}
.dashboard-container {{
  width: 100%;
  flex: 1;
  display: flex;
  flex-direction: column;
}}
.mono {{ font-family: var(--font-mono); }}
.sec-label {{ font-family: var(--font-mono); font-size: 11px; letter-spacing: 0.07em; color: var(--color-text-tertiary); margin: 0 0 10px; }}
.card {{ background: var(--color-background-primary); border: 0.5px solid var(--color-border-tertiary); border-radius: var(--border-radius-lg); padding: 14px 16px; }}
.stat-card {{ background: var(--color-background-secondary); border-radius: var(--border-radius-md); padding: 12px 14px; }}
.stat-label {{ font-family: var(--font-mono); font-size: 11px; letter-spacing: 0.05em; margin: 0 0 4px; }}
.stat-num {{ font-family: var(--font-mono); font-size: 22px; font-weight: 500; margin: 0; }}
.stat-sub {{ font-family: var(--font-mono); font-size: 11px; color: var(--color-text-tertiary); margin: 4px 0 0; }}
.ch-tag {{ display: inline-block; font-family: var(--font-mono); font-size: 10px; padding: 2px 8px; border-radius: 4px; background: var(--color-background-secondary); color: var(--color-text-secondary); border: 0.5px solid var(--color-border-tertiary); }}
.trow td {{ padding: 6px 8px; font-size: 12px; font-family: var(--font-mono); border-bottom: 0.5px solid var(--color-border-tertiary); }}
.trow:last-child td {{ border-bottom: none; }}

/* Pure CSS Donut Chart */
.donut {{
  width: 140px;
  height: 140px;
  border-radius: 50%;
  background: conic-gradient(
    #639922 0% {p1:.1f}%,
    #BA7517 {p1:.1f}% {p2:.1f}%,
    #D85A30 {p2:.1f}% {p3:.1f}%,
    #888780 {p3:.1f}% 100%
  );
  position: relative;
  margin: 0 auto;
}}
.donut::after {{
  content: "";
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 62%;
  height: 62%;
  background: var(--color-background-primary);
  border-radius: 50%;
}}

/* Pure CSS Bar Chart */
.bar-chart {{
  display: flex;
  flex-direction: column;
  gap: 10px;
  height: 100%;
  justify-content: center;
  margin-top: 10px;
}}
.bar-row {{
  display: flex;
  align-items: center;
  gap: 12px;
}}
.bar-label {{
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--color-text-secondary);
  width: 65px;
  text-align: right;
  flex-shrink: 0;
}}
.bar-track {{
  flex: 1;
  height: 14px;
  position: relative;
  border-left: 1px solid var(--color-border-secondary);
}}
.bar-fill {{
  height: 100%;
  background: #639922;
  border-radius: 0 3px 3px 0;
}}
.bar-val {{
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--color-text-tertiary);
  width: 35px;
}}
</style>
</head>
<body>

<div class="screenshot-wrapper">
<div class="dashboard-container">

  <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 1.25rem; padding-bottom: 12px; border-bottom: 0.5px solid var(--color-border-tertiary);">
    <span style="font-family: var(--font-mono); font-size: 14px; color: var(--color-text-secondary); letter-spacing: 0.08em; font-weight: bold;">NETWORK_SCORER</span>
    <span style="font-family: var(--font-mono); font-size: 12px; color: var(--color-text-tertiary);">v1.1.1</span>
    <div style="margin-left: auto; display: flex; align-items: center; gap: 8px;">
      <span style="font-family: var(--font-mono); font-size: 10px; color: #BA7517; padding: 4px 8px; background: rgba(186,117,23,0.1); border-radius: 4px; border: 0.5px solid rgba(186,117,23,0.2); letter-spacing: 0.05em;">PUBLIC SAFE MODE</span>
    </div>
  </div>

  <div style="display: grid; grid-template-columns: repeat(7, 1fr); gap: 10px; margin-bottom: 1.25rem;">
    <div class="stat-card"><p class="stat-label" style="color:var(--color-text-tertiary);">TOTAL</p><p class="stat-num" style="color:var(--color-text-primary);">{observed_contacts}</p><p class="stat-sub">observed</p></div>
    <div class="stat-card"><p class="stat-label" style="color:var(--color-text-secondary);">CURRENT FRIENDS</p><p class="stat-num" style="color:var(--color-text-primary);">{num_current}</p><p class="stat-sub">friends</p></div>
    <div class="stat-card"><p class="stat-label" style="color:#3B6D11;">KEEP</p><p class="stat-num" style="color:#639922;">{len(keep)}</p><p class="stat-sub">{keep_pct:.1f}%</p></div>
    <div class="stat-card"><p class="stat-label" style="color:#854F0B;">REVIEW</p><p class="stat-num" style="color:#BA7517;">{len(review)}</p><p class="stat-sub">{review_pct:.1f}%</p></div>
    <div class="stat-card"><p class="stat-label" style="color:#993C1D;">STALE</p><p class="stat-num" style="color:#D85A30;">{len(stale)}</p><p class="stat-sub">{stale_pct:.1f}%</p></div>
    <div class="stat-card"><p class="stat-label" style="color:var(--color-text-secondary);">UNKNOWN</p><p class="stat-num" style="color:#888780;">{len(unknown)}</p><p class="stat-sub">{unknown_pct:.1f}%</p></div>
    <div class="stat-card"><p class="stat-label" style="color:var(--color-text-tertiary);">OBSERVED CONTACTS</p><p class="stat-num" style="color:var(--color-text-primary);">{non_friend_contacts}</p><p class="stat-sub">non-friend</p></div>
  </div>

  <div style="display: grid; grid-template-columns: 220px 1fr; gap: 12px; margin-bottom: 12px;">
    <div class="card" style="display:flex;flex-direction:column;">
      <p class="sec-label">SPLIT</p>
      <div style="display:flex;flex-direction:column;gap:8px;margin-bottom:20px;">
        <span style="display:flex;align-items:center;gap:6px;font-size:12px;font-family:var(--font-mono);color:var(--color-text-secondary);"><span style="width:10px;height:10px;border-radius:2px;background:#639922;flex-shrink:0;"></span>keep {len(keep)}</span>
        <span style="display:flex;align-items:center;gap:6px;font-size:12px;font-family:var(--font-mono);color:var(--color-text-secondary);"><span style="width:10px;height:10px;border-radius:2px;background:#BA7517;flex-shrink:0;"></span>review {len(review)}</span>
        <span style="display:flex;align-items:center;gap:6px;font-size:12px;font-family:var(--font-mono);color:var(--color-text-secondary);"><span style="width:10px;height:10px;border-radius:2px;background:#D85A30;flex-shrink:0;"></span>stale {len(stale)}</span>
        <span style="display:flex;align-items:center;gap:6px;font-size:12px;font-family:var(--font-mono);color:var(--color-text-secondary);"><span style="width:10px;height:10px;border-radius:2px;background:#888780;flex-shrink:0;"></span>unknown {len(unknown)}</span>
      </div>
      <div style="flex:1; display:flex; align-items:center; justify-content:center; min-height: 160px;">
        <div class="donut"></div>
      </div>
    </div>

    <div class="card">
      <p class="sec-label">TOP CONNECTIONS — interaction_score (log scale)</p>
      <div class="bar-chart">
        {bar_html}
      </div>
    </div>
  </div>

  <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px;">
    <div class="card">
      <p class="sec-label" style="color:#854F0B;">REVIEW — cần cân nhắc</p>
      <table style="width:100%;border-collapse:collapse;table-layout:fixed;">
        <thead><tr style="border-bottom:0.5px solid var(--color-border-tertiary);">
          <th style="text-align:left;padding:3px 8px;font-size:10px;font-family:var(--font-mono);font-weight:400;color:var(--color-text-tertiary);width:42%;">node_id</th>
          <th style="text-align:right;padding:3px 8px;font-size:10px;font-family:var(--font-mono);font-weight:400;color:var(--color-text-tertiary);width:18%;">score</th>
          <th style="text-align:right;padding:3px 8px;font-size:10px;font-family:var(--font-mono);font-weight:400;color:var(--color-text-tertiary);width:12%;">sig</th>
          <th style="text-align:left;padding:3px 8px;font-size:10px;font-family:var(--font-mono);font-weight:400;color:var(--color-text-tertiary);width:28%;">channels</th>
        </tr></thead>
        <tbody>
          {review_html}
        </tbody>
      </table>
    </div>

    <div class="card">
      <p class="sec-label">TOP STALE — cao nhất trong nhóm im lặng</p>
      <table style="width:100%;border-collapse:collapse;table-layout:fixed;">
        <thead><tr style="border-bottom:0.5px solid var(--color-border-tertiary);">
          <th style="text-align:left;padding:3px 8px;font-size:10px;font-family:var(--font-mono);font-weight:400;color:var(--color-text-tertiary);width:40%;">node_id</th>
          <th style="text-align:right;padding:3px 8px;font-size:10px;font-family:var(--font-mono);font-weight:400;color:var(--color-text-tertiary);width:18%;">score</th>
          <th style="text-align:right;padding:3px 8px;font-size:10px;font-family:var(--font-mono);font-weight:400;color:var(--color-text-tertiary);width:12%;">sig</th>
          <th style="text-align:left;padding:3px 8px;font-size:10px;font-family:var(--font-mono);font-weight:400;color:var(--color-text-tertiary);width:30%;">channels</th>
        </tr></thead>
        <tbody>
          {stale_html}
        </tbody>
      </table>
    </div>
  </div>

  <div class="card">
    <p class="sec-label">UNKNOWN — zero signal ({len(top_unknown)} nodes)</p>
    <div style="display:flex;flex-wrap:wrap;gap:8px;">
      {unknown_html}
    </div>
  </div>

</div>
</div>

</body>
</html>
"""
    
    dashboard_path = output_dir / "dashboard_public_safe.html"
    with open(dashboard_path, "w", encoding="utf-8") as f:
        f.write(html_content)
        
    return dashboard_path
