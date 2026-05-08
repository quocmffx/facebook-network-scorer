# Facebook Network Scorer

Phân tích Facebook export JSON và scoring mức độ "kết nối còn hoạt động" trong network cá nhân.

## Mục tiêu

- Đo tín hiệu tương tác thật
- Phát hiện network noise
- Hỗ trợ reset audience/context
- Phân loại: keep / review / stale / unknown

## Cài đặt

```bash
pip install -r requirements.txt
```

## Chạy

```bash
# Từ thư mục chứa Facebook export
python -m fb_network_scorer . --output ./scored_output

# Hoặc chỉ định đường dẫn
python -m fb_network_scorer "C:\path\to\facebook-export" -o "C:\output"
```

## Output

| File | Mô tả |
|---|---|
| `fb_friend_score.csv` | Toàn bộ contacts + scores |
| `keep.csv` | Kết nối hoạt động, multi-channel |
| `review.csv` | Có lịch sử nhưng yếu |
| `stale_connections.csv` | Gần như không còn tín hiệu |
| `unknown_no_signal.csv` | Thiếu data để phân loại |

## Scoring Model

### 1. Time Decay (Exponential)

```
weight = exp(-lambda * days_since_interaction)
lambda = 0.00385 (half-life ~ 180 ngày)
```

Tín hiệu cũ tự giảm giá trị theo thời gian. Half-life 180 ngày nghĩa là tương tác 6 tháng trước chỉ còn ~50% giá trị.

### 2. Message Score

- **Bidirectional bonus (x2.0)**: Hội thoại 2 chiều = tín hiệu mạnh nhất
- **One-sided penalty (x0.3)**: Spam 1 chiều bị phạt nặng
- **Recent boost (x1.5)**: Tin nhắn trong 90 ngày gần nhất được boost
- Channel weight: **5.0** (cao nhất)

### 3. Comment Score

- Comment dài >= 10 ký tự: weight **1.0** (tương tác thật)
- Comment ngắn/tag: weight **0.3** (weak signal)
- Time decay áp dụng trên trung bình
- Channel weight: **3.0**

### 4. Reaction Score

- Base weight: **0.2** (weak signal)
- Repeated reactions boost: `1 + 0.5 * log(1 + count)` (log scale, diminishing returns)
- Channel weight: **1.0** (thấp nhất)

### 5. Context Drift

```
Nếu last_interaction < 365 ngày: context = 100%
Nếu last_interaction > 365 ngày: giảm tuyến tính, floor 10%
Full decay sau ~3 năm không tín hiệu
```

Context score được dùng như multiplier cho composite score. Người từng active mạnh nhưng biến mất 3 năm bị giảm 90% giá trị.

### 6. Confidence

```
confidence = log(1 + total_signals) / log(1 + 20)
```

- 0 signals: confidence ~0.05
- 1 signal: ~0.23
- 5 signals: ~0.58
- 20+ signals: ~0.9+

Khi confidence < 0.3: không classify aggressively, đưa vào `unknown_no_signal`.

### 7. Classification Rules

| Classification | Điều kiện |
|---|---|
| **keep** | composite >= 40 HOẶC có DM 2 chiều trong 365 ngày gần nhất |
| **review** | composite >= 10 HOẶC từng có DM 2 chiều HOẶC confidence thấp nhưng có tín hiệu người thật (DM/comment) |
| **stale_connections** | composite < 10, không DM, không comment, chỉ reaction cũ hoặc zero signal |
| **unknown_no_signal** | thiếu tên / không match được / zero signal + zero confidence |

## Composite Score

```
raw_composite = message_score + comment_score + reaction_score
composite = raw_composite * (context_score / 100)
```

Context drift hoạt động như penalty multiplier. Một người có lịch sử tương tác mạnh nhưng context drift sẽ bị giảm composite tương ứng.

## Tradeoffs & Known Limitations

### False Positives (classified quá cao)

- **Page likes bị tính là friend reactions**: Nếu bạn like bài của 1 page có tên giống friend, score bị inflate. Mitigation: fuzzy matching threshold 80%.
- **Group chat noise**: Bỏ qua group chat (chỉ tính DM 2 người). Có thể miss tín hiệu từ bạn bè chỉ chat trong group.

### False Negatives (classified quá thấp)

- **Vietnamese name ambiguity**: 2 người tên giống nhau (VD: "Hoàng Vũ") có thể bị merge signals.
- **Missing data channels**: Facebook export không bao gồm story views, profile visits, video calls detail.
- **Comment title parsing**: Chỉ extract được tên từ comment title patterns cụ thể. Comments trên pages/groups mà không mention friend bị miss.

### Facebook Export Schema

- Schema thay đổi theo ngôn ngữ tài khoản (Vietnamese/English)
- Encoding: Double-encoded UTF-8 (mojibake) - code xử lý bằng latin-1 -> UTF-8 round-trip
- Một số file có thể bị thiếu tùy privacy settings
- Code graceful degrade khi thiếu folder/file

## Cấu trúc project

```
fb_network_scorer/
  __init__.py
  __main__.py        # CLI entry point
  config.py          # Scoring parameters
  parser.py          # Facebook JSON parsers
  scorer.py          # Scoring engine
  exporter.py        # CSV export
requirements.txt
README.md
```

## Tuning

Chỉnh parameters trong `config.py`:

```python
ScoringConfig(
    decay_lambda=0.00385,        # Tăng = decay nhanh hơn
    threshold_keep=40.0,         # Giảm = dễ classify "keep" hơn
    msg_bidirectional_bonus=2.0, # Tăng = ưu tiên 2-way chat mạnh hơn
    ...
)
```
