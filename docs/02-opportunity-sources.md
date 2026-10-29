# Nguồn cơ hội và cách xác minh

## Những nguồn đã nghiên cứu

| Nguồn | Đã xác minh từ tài liệu | Vai trò đề xuất | Giới hạn |
| --- | --- | --- | --- |
| [free-for-dev](https://github.com/ripienaar/free-for-dev) | Danh mục SaaS/PaaS/IaaS có free tiers; phạm vi loại free trial | Seed URLs và taxonomy | Không phải API giveaway; danh mục có thể lỗi thời; không chứng minh user đủ điều kiện |
| [GitHub Education](https://github.com/github/docs/blob/main/content/education/about-github-education/github-education-for-students/apply-to-github-education-as-a-student.md) | Có điều kiện nhập học, tài khoản cá nhân, độ tuổi và bằng chứng tư cách; email học thuật tùy quy trình | Case study eligibility và human handoff | Không phải API đăng ký tổng quát; không được xem email sinh viên là bằng chứng đủ cho mọi chương trình |
| [Hacker News API](https://github.com/HackerNews/API) | Public API v0, items và danh sách stories | Discovery các bài giới thiệu sản phẩm/chương trình | Không có endpoint search được tài liệu này mô tả; nội dung cộng đồng không là bằng chứng chính thức |
| [GitHub REST API description](https://github.com/github/rest-api-description) | Repository cung cấp mô tả OpenAPI của REST API | Tham khảo khi làm connector GitHub | Đây không phải danh mục cơ hội; vẫn phải đọc endpoint/auth/rate-limit cụ thể trước khi triển khai |

Trang pricing, benefits, chương trình startup và announcement của nhà cung cấp là nguồn xác minh đề xuất. Nghiên cứu này chưa xác nhận một danh sách ưu đãi cụ thể còn hiệu lực.

## Những nguồn chỉ mới là ứng viên

Devpost, MLH, trang chương trình startup, newsletter, Reddit, Discord và các nền tảng giveaway có thể hữu ích. **Chưa kiểm chứng API, điều khoản, quyền crawl, chất lượng hay chi phí** của những nguồn này. Không viết connector dựa trên API phỏng đoán hoặc giả định nội dung public đồng nghĩa được phép tự đăng ký.

## Pipeline dữ liệu đề xuất

1. Khám phá URL qua danh mục/API công khai hoặc URL người dùng nhập.
2. Chuẩn hóa URL, loại tracking; giữ bản gốc và redirect chain để truy vết.
3. Chỉ fetch destination được phép; chặn private IP, metadata endpoint và redirect vượt phạm vi ở tầng mạng.
4. Đọc trang chính thức, điều kiện và form liên quan; tôn trọng điều khoản, robots và rate limits. Robots không tự cấp quyền gửi form.
5. Trích xuất vào schema, lưu evidence cho từng field quan trọng.
6. Khử trùng lặp theo organizer, program và campaign/version; URL giống nhau chưa chắc là cùng đợt.
7. Kiểm tra eligibility theo hồ sơ; giữ `unknown` khi thiếu thông tin.
8. Revalidate ngay trước khi submit, nhất là deadline, consent, reward và destination.

## Schema nghiên cứu đề xuất

| Nhóm | Trường cần có |
| --- | --- |
| Identity | opportunity_id, organizer, canonical_url, campaign_id, type |
| Value | reward_description, currency/unit, guaranteed_or_conditional, expiry |
| Timing | deadline_raw, deadline_at, timezone, last_checked_at |
| Eligibility | countries, age/student/startup requirements, required_evidence |
| Action | application_url, required_fields, login_required, automation_status |
| Evidence | source_url, retrieved_at, content_hash, excerpt, field_name |
| Lifecycle | discovered, verified, stale, closed, rejected |

`automation_status` nên có `allowed / prohibited / unknown`; nguồn không nói gì không có nghĩa là allowed. Deadline thiếu timezone cần làm rõ, không tự gán UTC. Không có deadline khác với không biết deadline.

## Đánh giá độ tin cậy

Không gộp mọi thứ vào một điểm “legit 95%”. Tách: nguồn có chính thức không, nội dung có mới không, user có đủ điều kiện không, hành động có được cấp quyền không. HTTPS hay logo thương hiệu không đủ chứng minh uy tín.

Một cộng đồng có thể đưa ra lead tốt; agent vẫn phải đối chiếu tên miền chính thức, organizer và terms. Nếu nguồn mâu thuẫn, lưu cả hai và tạm dừng quyết định thay vì chọn nội dung thuận lợi hơn.

## Công việc thu thập tiếp theo

Tạo tập 20–30 ứng viên; ghi lại số còn hoạt động, có nguồn chính thức, phù hợp Việt Nam, không yêu cầu thẻ và có đường đăng ký khả thi. Chưa thu thập tập này trong đợt research tài liệu hiện tại. Đây là bước xác minh cung dữ liệu trước khi hứa hẹn độ phủ.
