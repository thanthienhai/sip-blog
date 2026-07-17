# Family & Relationships

Bộ 100 mục từ tiếng Anh về gia đình và các mối quan hệ, chia thành 7 chủ đề:

- `immediate_family`: gia đình gần gũi
- `extended_family`: họ hàng và gia phả
- `life_events`: các giai đoạn và sự kiện gia đình
- `social_relationships`: quan hệ xã hội
- `parenting`: nuôi dạy và chăm sóc
- `conflict_resolution`: xung đột và hòa giải
- `values_emotions`: giá trị và cảm xúc

Các file Anki:

- `SIP-Family-Relationships-Basic-Reversed.apkg`: Anh → Việt và Việt → Anh
- `SIP-Family-Relationships-Sentence-Mining.apkg`: điền từ/cụm từ vào câu; phát âm xuất hiện sau khi trả lời
- `SIP-Family-Relationships-Comprehensive.apkg`: nghĩa, IPA, ví dụ và cụm từ hữu ích

Mỗi bộ có 100 ảnh minh họa và 100 tệp MP3 phát âm tiếng Anh được nhúng trực
tiếp. Ảnh trên mặt câu hỏi hỗ trợ gợi nhớ; các thẻ điền từ không phát âm thanh
trước khi trả lời để tránh làm lộ đáp án.

Các ảnh tải từ Openverse có ghi nguồn và giấy phép trong
`media/image_attributions.json`; các ảnh minh họa riêng còn lại nằm trong
`media/images`.

Tạo lại cả ba file bằng Python 3 (không cần cài thêm thư viện):

```bash
python3 'Family&Relationships/build_family_relationships_anki.py'
```

Script tự kiểm tra dữ liệu nguồn và từng file sau khi đóng gói: số lượng
note/card, SQLite integrity, model/deck ID, trường dữ liệu, tag, thứ tự học,
trạng thái scheduling sạch và mọi tham chiếu hình/âm thanh.
