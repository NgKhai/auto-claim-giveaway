# Các phương án kỹ thuật — chưa chốt thiết kế

## So sánh ba hướng

| Hướng | Ưu điểm | Đánh đổi |
| --- | --- | --- |
| A. Discovery + đánh giá + link/điền nháp | Ít phụ thuộc website, dễ kiểm chứng nguồn | Chưa chứng minh phần tự đăng ký trọn hành trình |
| B. Discovery + policy + adapter theo website | Luồng gửi form kiểm thử được, bằng chứng rõ | Độ phủ ban đầu thấp; phải bảo trì adapter |
| C. Browser agent tổng quát | Tiềm năng xử lý nhiều cấu trúc form | Khó dự đoán thành công, chi phí, consent và tác động của thay đổi trang |

**Khuyến nghị nghiên cứu: B**, với A làm fallback. C là một spike riêng, chưa phải cam kết sản phẩm. Người dùng chưa chọn phương án hoặc duyệt thiết kế triển khai.

## Stack ứng viên

- Hướng TypeScript: web app + API, OpenAI Agents SDK JS, Playwright, PostgreSQL và một job worker. Inngest chỉ thêm nếu nhu cầu retry/scheduling thực tế đáng để thêm dependency.
- Hướng Python: web frontend + Python API, Agents SDK Python, Playwright Python; Crawl4AI nếu thử nghiệm extraction cho kết quả tốt.
- Chưa cần vector DB: lọc cấu trúc, tìm kiếm văn bản và evidence storage đủ để kiểm chứng MVP nhỏ.
- Một orchestrator với tools riêng là đủ để thử nghiệm đầu; không cần nhiều agent chỉ để đặt tên vai trò.

Đây là lựa chọn đề xuất dựa trên khả năng tài liệu, chưa có cài đặt hoặc benchmark.

## Ranh giới trách nhiệm đề xuất

Discovery tạo candidate; verifier tạo facts có evidence; policy engine quyết định hành động hợp lệ; executor thực hiện action đã được duyệt; tracker cập nhật trạng thái; notifier gửi nội dung qua kênh được cấu hình.

LLM xử lý nội dung và đề xuất; quyền hành động được kiểm tra bằng code phía server tại thời điểm thực thi. Không giao quyết định consent hoàn toàn cho prompt hoặc điểm confidence.

## Policy tối thiểu

Mỗi authorization lưu user, mục đích, domain, action, trường dữ liệu được gửi, thời hạn và phiên bản policy. Approval cần gắn với payload/form version cụ thể; form thêm consent hoặc redirect sang domain khác làm approval cũ không còn đủ.

Phân biệt ba quyền: đọc trang, điền dữ liệu và submit. Quyền của user không thay thế điều khoản automation của website. Thiếu hồ sơ, CAPTCHA, OTP, giấy tờ hoặc yêu cầu thanh toán dẫn đến handoff đúng bước.

Nội dung website/email là dữ liệu không tin cậy: không được nâng quyền, đọc secrets hoặc điều khiển tools theo chỉ dẫn nhúng. Browser egress phải chặn private destinations, kiểm tra redirect và cô lập sessions; bộ lọc của MCP không đủ làm boundary.

## State và tác dụng phụ

Vòng đời application đề xuất:

`draft → awaiting_approval → ready → submitting → submitted → pending_review → approved/rejected`

Các trạng thái bổ sung: `needs_user_action`, `submission_unknown`, `expired`, `failed`. Phân biệt approval của người dùng với approval của bên tổ chức. `approved` cũng chưa chứng minh quyền lợi đã được cấp; lưu fulfillment riêng như `available / claimed / expired` cùng bằng chứng.

Mỗi lần submit có action ID, khóa theo user + campaign và fingerprint payload. Đánh dấu attempt trước khi thực thi, lưu receipt sau đó. Nếu timeout sau khi bấm gửi, chuyển `submission_unknown`; reconcile bằng trạng thái/receipt trước khi retry. Unique key trong DB không bảo đảm exactly-once ở website bên ngoài.

## Audit và dữ liệu cá nhân

Lưu evidence IDs, rule/version đã áp dụng, action, timestamp, trạng thái và receipt; không cần lưu suy luận nội bộ dài của model. Structured reason đủ để giải thích quyết định.

Giới hạn PII gửi vào model, mã hóa credentials, che thông tin nhạy cảm trong artifact, đặt retention và cơ chế xóa dữ liệu. Trace của framework phục vụ debug; application audit phục vụ giải thích trạng thái và quyền hành động.

## Những gì phải thử trước khi chốt

Khả năng trích điều kiện, tỷ lệ sửa form đúng, resume sau restart, duplicate submission prevention, isolation, policy enforcement và độ chính xác ghép confirmation. Chưa có bằng chứng thực nghiệm cho những khả năng này trong repository.
