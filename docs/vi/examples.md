# Ví dụ

## Cách dùng cơ bản
Để công cụ phân tích dữ liệu Facebook của bạn và xuất các tệp CSV vào thư mục `ket_qua`:

```bash
fb-network-scorer /duong/dan/toi/thu-muc-giai-nen --output ./ket_qua
```

## Chạy lệnh Doctor
Nếu bạn không chắc chắn liệu mình đã tải đúng định dạng dữ liệu hay chưa, bạn có thể chạy công cụ chẩn đoán. Lệnh `doctor` chỉ thực hiện kiểm tra cấu trúc thư mục một cách an toàn mà không đọc bất kỳ nội dung tin nhắn nào của bạn.

```bash
fb-network-scorer doctor /duong/dan/toi/thu-muc-giai-nen
```

## Dữ liệu mẫu (Synthetic Data)
Kho lưu trữ này có chứa sẵn một tập dữ liệu giả do chúng tôi tạo ra. Bạn có thể tự mình chạy thử công cụ để xem cách hoạt động:

```bash
fb-network-scorer examples/sample_export --output ./examples/sample_output
```
