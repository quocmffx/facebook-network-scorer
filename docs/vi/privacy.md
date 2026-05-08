# Ranh giới Quyền riêng tư

**Phần mềm tĩnh lặng dành cho những hệ thống ồn ào. Hoạt động hoàn toàn cục bộ. An toàn quyền riêng tư.**

Dự án này được xây dựng trên nguyên tắc: dữ liệu xã hội của bạn thuộc về bạn và tuyệt đối không bao giờ bị phơi bày ra mạng internet.

## 1. Chỉ xử lý cục bộ
Facebook Network Scorer là một ứng dụng dòng lệnh hoạt động 100% trên máy tính cá nhân của bạn.
- Không có luồng tải lên đám mây (cloud uploads).
- Không thu thập dữ liệu phân tích (telemetry) hay theo dõi.
- Không yêu cầu API key.
- Không tạo bất kỳ kết nối mạng nào ra bên ngoài trong suốt quá trình chấm điểm.

## 2. Tuyệt đối không Commit dữ liệu cá nhân
Bạn **không bao giờ được phép commit** dữ liệu sao lưu thật của Facebook lên Git hay bất kỳ máy chủ công cộng nào. Tệp `.gitignore` đã được cấu hình vô cùng khắt khe để tự động loại bỏ các thư mục xuất dữ liệu mặc định (`facebook-*`, `your_facebook_activity`, v.v.).

## 3. Giao diện (Dashboard)
Nếu bạn xây dựng giao diện hiển thị trên bộ đếm điểm này, hãy đảm bảo rằng nó chỉ hoạt động dưới dạng file HTML/CSS tĩnh và lưu trữ trên máy bạn. Không sử dụng các CDN bên ngoài và không nhúng các đoạn mã theo dõi (analytics) của bên thứ ba. Hãy giữ mọi thứ đơn giản và an toàn.
