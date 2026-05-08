# facebook-network-scorer

[English](README.md) | [Tiếng Việt](README.vi.md)

Công cụ chấm điểm tương tác trên biểu đồ xã hội Facebook của bạn dựa trên dữ liệu thật.

Phần mềm tĩnh lặng dành cho những hệ thống ồn ào (Quiet tools for noisy systems). Hoạt động hoàn toàn trên máy cá nhân, đảm bảo an toàn quyền riêng tư.

Phân tích dữ liệu JSON trích xuất từ **"Tải thông tin của bạn xuống" (Download Your Information)** của Facebook/Meta và tạo ra điểm số cho từng người bạn dựa trên:

- **Độ mạnh tín hiệu** - tin nhắn, bình luận, cảm xúc được đánh trọng số theo từng kênh.
- **Lọc nhiễu** - bỏ qua tin nhắn rác một chiều, tag ngắn, cảm xúc trên trang.
- **Suy giảm theo thời gian** - giảm dần trọng số theo thời gian với chu kỳ bán rã có thể cấu hình.
- **Trôi dạt ngữ cảnh** - phát hiện những kết nối đã nguội lạnh theo năm tháng.
- **Tương tác hai chiều** - ưu tiên những cuộc trò chuyện qua lại thực sự.

## Bắt đầu nhanh

```bash
pip install -r requirements.txt
python -m fb_network_scorer /path/to/facebook-export --output ./scored_output
```

Hoặc kiểm tra tính hợp lệ của dữ liệu trích xuất:

```bash
python -m fb_network_scorer doctor /path/to/facebook-export
```

### Tùy chọn: Cài đặt toàn cục (Global installation)

```bash
pip install -e .
fb-network-scorer /path/to/facebook-export --output ./scored_output
fb-network-scorer doctor /path/to/facebook-export
```

*(Lưu ý: Lệnh `doctor` chỉ kiểm tra cấu trúc thư mục và siêu dữ liệu, tuyệt đối không quét nội dung tin nhắn riêng tư).*

## Trích xuất dữ liệu Facebook

Trước khi chạy công cụ, bạn cần có một bản sao lưu dữ liệu Facebook định dạng JSON.

Xem **[docs/vi/export-facebook-data.md](docs/vi/export-facebook-data.md)** để biết hướng dẫn chi tiết từng bước, bao gồm:

- Những danh mục cần chọn (Bạn bè, Tin nhắn, Bình luận, Cảm xúc, ...)
- Cài đặt định dạng (JSON, Chất lượng thấp, Khoảng thời gian)
- Quy tắc quyền riêng tư và những điều tuyệt đối không đưa lên Git.

## Đầu ra (Output)

| Tập tin | Mô tả |
|---|---|
| `current_friends_scored.csv` | Toàn bộ bạn bè hiện tại kèm điểm số |
| `current_friends_keep.csv` | Nên giữ: Tương tác tích cực, đa kênh |
| `current_friends_review.csv` | Cần xem xét: Tương tác yếu hoặc không rõ ràng |
| `current_friends_stale.csv` | Đã nguội: Từng tương tác nhưng đã lâu không trò chuyện |
| `unknown_no_signal.csv` | Không đủ dữ liệu để phân loại |
| `non_friend_contacts.csv` | Trang, nhóm, hoặc những người không kết bạn |

## Cấu trúc dự án

```
fb_network_scorer/
  __init__.py       # Thông tin gói phần mềm
  __main__.py       # Entry point
  cli.py            # Logic giao diện dòng lệnh
  config.py         # Tất cả tham số cấu hình chấm điểm
  models.py         # Cấu trúc dữ liệu
  parser.py         # Trình phân tích JSON (xử lý lỗi font chữ)
  scorer.py         # Engine chấm điểm với logic thời gian và ngữ cảnh
  exporter.py       # Xuất file CSV phân loại

examples/
  sample_export/    # Dữ liệu giả để kiểm thử

docs/
  vi/               # Tài liệu Tiếng Việt
```

## Quyền riêng tư (Privacy)

> **Cảnh báo:** Ranh giới quyền riêng tư là tuyệt đối. Không bao giờ commit dữ liệu Facebook thật, kết quả CSV thật, hoặc tên thật lên kho lưu trữ này. 

Mọi dữ liệu cá nhân của bạn sẽ chỉ nằm trên máy tính của bạn. Không có luồng tải lên đám mây (cloud upload) và không có dữ liệu nào rời khỏi thiết bị của bạn. File `.gitignore` đã được cấu hình để tự động loại trừ các tệp xuất Facebook.

Đọc thêm tại [docs/vi/privacy.md](docs/vi/privacy.md).

## Bản quyền

[MIT](LICENSE)

## Liên kết

- Trang chủ: [greenjade.net](https://greenjade.net)
