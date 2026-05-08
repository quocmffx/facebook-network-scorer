# Mô hình Chấm điểm (Scoring Model)

Facebook Network Scorer sử dụng một thuật toán đa kênh để tính toán mức độ tương tác giữa bạn và những người kết nối.

## Kênh tín hiệu và Trọng số

Các tương tác được phân tích và đánh trọng số dựa trên giá trị của chúng:
- **Tin nhắn trực tiếp (Direct Messages):** Tín hiệu mạnh nhất để xác định một mối quan hệ thực sự.
- **Bình luận:** Tín hiệu trung bình. Những bình luận dài sẽ có trọng số cao hơn các tag ngắn.
- **Cảm xúc (Reactions):** Tín hiệu yếu nhất, thể hiện các tương tác "tiện tay" (like, love, v.v.).

## Các khái niệm cốt lõi

### Tính điểm tương tác hai chiều (Bidirectional Scoring)
Thuật toán ưu tiên và thưởng điểm cho các cuộc trò chuyện diễn ra từ hai phía. Một cuộc nói chuyện mà cả hai cùng tham gia tích cực sẽ nhận được hệ số nhân lớn. Ngược lại, những đoạn spam một chiều hay tự nói một mình sẽ bị trừ điểm nặng.

### Suy giảm theo thời gian (Time Decay)
Tất cả tín hiệu tương tác đều giảm dần trọng số theo thời gian thông qua một hàm suy giảm. Một cuộc nói chuyện từ ngày hôm qua sẽ mang giá trị lớn hơn rất nhiều so với một bình luận từ 5 năm trước.

### Trôi dạt ngữ cảnh (Context Drift)
Khi bạn ngừng tương tác hoàn toàn với một người trong một thời gian dài, điểm trôi dạt ngữ cảnh của họ sẽ tăng lên. Điều này giúp đẩy những mối quan hệ lịch sử vào danh sách `current_friends_stale.csv` (những mối quan hệ đã nguội lạnh), giúp bạn có cái nhìn rõ ràng hơn về những người thực sự còn tương tác trong hiện tại.
