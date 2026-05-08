# Hướng dẫn xuất dữ liệu Facebook

Để công cụ chấm điểm hoạt động, bạn cần cung cấp một bản sao lưu dữ liệu cá nhân từ Facebook.

## Các bước thực hiện

1. Truy cập **Cài đặt & quyền riêng tư** trên Facebook.
2. Chọn **Trung tâm tài khoản** > **Thông tin và quyền của bạn**.
3. Nhấp vào **Tải thông tin của bạn xuống**.
4. Chọn **Tải xuống hoặc chuyển thông tin**.
5. Chọn **Thông tin cụ thể** (Đừng chọn "Tất cả thông tin" vì file sẽ rất lớn).
6. Tích chọn các mục sau:
   - Bài viết
   - Tin nhắn
   - Bình luận và cảm xúc
   - Bạn bè và người theo dõi
   - Thông tin cá nhân
7. Nhấn **Tiếp**. Chọn **Tải xuống thiết bị**.
8. Tùy chỉnh cài đặt tải xuống:
   - Khoảng thời gian: Tùy chọn (khuyên dùng Từ trước đến nay).
   - Định dạng: **JSON** (Bắt buộc).
   - Chất lượng phương tiện: **Thấp** (để giảm thời gian tải).
9. Nhấn **Tạo file**.

Khi Facebook thông báo file đã sẵn sàng, hãy tải xuống và giải nén thư mục.

## Chạy lệnh Doctor

Để đảm bảo bạn đã tải đúng thư mục, hãy chạy lệnh kiểm tra:

```bash
fb-network-scorer doctor /duong/dan/toi/thu-muc-giai-nen
```

## Chạy công cụ chấm điểm

```bash
fb-network-scorer /duong/dan/toi/thu-muc-giai-nen --output ./ket_qua
```

> **Lưu ý bảo mật:** Tuyệt đối không chia sẻ thư mục bạn đã tải xuống cho bất kỳ ai. Dữ liệu này chứa toàn bộ tin nhắn riêng tư của bạn.
