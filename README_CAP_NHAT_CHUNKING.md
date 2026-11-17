# Cập nhật luồng xử lý PDF / RAG

## Các thay đổi
- Chia chunk theo tokenizer `intfloat/multilingual-e5-base`, giới hạn 380 token (đã tính prefix `passage:` và special tokens), overlap mục tiêu 60 token.
- Giữ thông tin trang, tên tài liệu; bổ sung `document_id` ổn định theo tên file, `content_hash`, `token_count` và `source_id` tùy chọn.
- `source_id` không tự suy diễn. Chỉ gán sau khi đối chiếu được với bảng `Event_Sources`.
- Embedding kiểm tra số token trước khi encode để tránh truncation im lặng.
- ChromaDB lưu metadata bổ sung; khi xử lý lại cùng tên tài liệu, chunk phiên bản cũ được dọn sau khi các chunk mới đã lưu thành công.
- Bổ sung các hàm API `/documents/embed` và `/documents/store` mà router hiện đang gọi nhưng service trước đó chưa có.
- Retrieval/context/answer giữ lại `source_id` nếu nguồn đã được ánh xạ.

## Cài đặt
Trong thư mục `backend`:

```bash
pip install -r requirement.txt
```

Các dependency thêm vào: `numpy`, `torch`, `transformers`, `sentence-transformers`.

## Thay file
Giải nén ZIP này tại thư mục gốc project, cho phép ghi đè theo đúng đường dẫn `backend/...`.

## Lưu ý dữ liệu
- Không thay đổi workbook Excel hoặc schema node/relationship của Neo4j.
- Không tự tạo node `NguonTaiLieu`; workbook hiện có sheet `Event_Sources` là bảng ánh xạ sự kiện–nguồn, không phải sheet node nguồn độc lập.
- `source_id` hiện để `None` cho đến khi có logic đối chiếu chắc chắn với `Event_Sources`.
- `document_id` được tạo ổn định theo tên file. Nếu có hai tài liệu độc lập trùng tên file, cần bổ sung định danh upload/nguồn file để phân biệt chúng.
- Chunk cũ đã lưu trong ChromaDB mà không có metadata `document_id` sẽ không tự bị xóa bởi cơ chế dọn phiên bản mới; cần rà soát riêng nếu muốn dọn dữ liệu legacy.

## Kiểm tra đã thực hiện
- `python -m compileall -q app`: đạt.
- Kiểm thử cấu trúc chunk bằng tokenizer giả lập offline: đạt (đây không thay thế kiểm thử tokenizer/model thật).
- Cần chạy thử tích hợp trên môi trường backend có cài đầy đủ dependency và tải được model E5 trước khi đưa lên production.
