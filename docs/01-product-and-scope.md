# Bài toán và phạm vi đề xuất

## Nhu cầu và giả thuyết

Người dùng biết mục tiêu của mình nhưng khó tìm cơ hội phù hợp, đọc điều kiện và theo dõi nhiều hạn chót. Giá trị cần kiểm chứng là giảm thời gian từ nhu cầu đến một hồ sơ hợp lệ, không chỉ tăng số liên kết tìm được.

Hai cách vào sản phẩm đã được nêu: tìm theo mục tiêu và đề xuất theo sở thích. Đề xuất nghiên cứu: kiểm chứng tìm theo mục tiêu trước vì có thể đo relevance bằng yêu cầu đầu vào rõ ràng.

Ví dụ: “Tìm tài nguyên miễn phí để build coding agent; tôi ở Việt Nam; không dùng thẻ; chỉ cho phép gửi tên và email tới nhà cung cấp được duyệt.” Đây là kịch bản giả định, không phải hồ sơ thật của người dùng.

## Phải phân biệt loại cơ hội

| Loại | Giá trị thực tế | Thông tin không được bỏ qua |
| --- | --- | --- |
| Free tier | Quyền sử dụng trong hạn mức | Reset quota, giới hạn vùng, phí vượt mức |
| Free trial | Truy cập tạm thời | Hạn dùng, thẻ thanh toán, gia hạn |
| Promotional credits | Số dư có điều kiện | Expiry, dịch vụ áp dụng, eligibility |
| Student benefits | Quyền lợi theo tư cách sinh viên | Bằng chứng, thời hạn tư cách, quy trình duyệt |
| Giveaway | Cơ hội trúng thưởng | Xác suất thường không biết, thời điểm công bố, giới hạn khu vực |
| Hackathon/grant | Cơ hội cần đầu tư công sức hoặc xét duyệt | Deliverables, tiêu chí, hạn nộp, quyền sử dụng bài dự thi |

Không cộng giá trị giải thưởng có xác suất với credits chắc chắn sử dụng được. Không tự suy ra xác suất thắng từ số người tương tác.

## Phạm vi MVP để kiểm chứng, chưa được chốt

- Một nhóm người dùng: developer/sinh viên làm dự án AI; chưa mặc định mọi người đều là sinh viên.
- Nhập mục tiêu, một hồ sơ tối thiểu và phạm vi hành động cho phép.
- Thu thập từ một danh mục discovery và một nhóm trang chính thức nhỏ.
- Hiển thị reward, hạn chót, điều kiện, bằng chứng và thông tin còn thiếu.
- Điền nháp; chỉ submit tự động trên adapter có kiểm thử và được người dùng cho phép.
- Theo dõi receipt/application ID, nhắc hạn và yêu cầu bổ sung.
- Thông báo trong app trước; email/Discord là tích hợp mở rộng.

Chưa đưa vào bản đầu: tạo hàng loạt tài khoản, tự đăng bài mạng xã hội, tự nộp giấy tờ, tự dùng thẻ, tự nhận tiền hoặc triển khai trên mọi website.

## Điểm khác biệt cần chứng minh

Các project ở [bảng tham khảo](03-reference-projects.md) chủ yếu cung cấp danh mục, crawling, browser hoặc orchestration. Đây là so sánh theo chức năng đọc được, không phải khảo sát đầy đủ đối thủ thị trường.

Sản phẩm này có thể khác biệt ở việc kết nối **hồ sơ cá nhân + bằng chứng điều kiện + quyền hành động + xác nhận kết quả**. Lịch sử phải giải thích được “vì sao phù hợp”, “vì sao được gửi”, “đã gửi dữ liệu gì” và “bằng chứng nào xác nhận trạng thái”.

## Các câu hỏi chưa có bằng chứng

- Người dùng ưu tiên tiết kiệm thời gian hay tối đa hóa giá trị quyền lợi?
- Có đủ cơ hội mới mỗi tuần để họ quay lại không?
- Bao nhiêu chương trình cho phép automation và bao nhiêu chương trình cần tương tác thủ công?
- Hackathon yêu cầu dùng Codex ở quá trình phát triển hay trong runtime sản phẩm? Cần đọc thể lệ chính thức trước khi chốt.
