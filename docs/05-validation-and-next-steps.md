# Thử nghiệm tính khả thi và bước tiếp theo

Đây là danh sách nghiên cứu cần thực hiện sau, không phải test report. Đợt này chỉ xác minh truy cập/đọc tài liệu; **chưa chạy app, adapter hoặc đăng ký thật**.

## 1. Kiểm chứng nguồn cung

Lập 20–30 ứng viên theo cách lấy mẫu được ghi rõ; giữ cả những ứng viên bị loại. Mỗi record gồm nguồn discovery, nguồn chính thức, last checked, loại quyền lợi, điều kiện, vùng, deadline, yêu cầu thanh toán và automation terms.

Đo: tỷ lệ còn hoạt động, tỷ lệ có terms rõ, tỷ lệ phù hợp hồ sơ mục tiêu và số nguồn cần để có một cơ hội dùng được. Tập nhỏ này giúp ra quyết định MVP, chưa đại diện toàn thị trường.

## 2. Ground truth cho extraction và eligibility

Người kiểm tra gán nhãn các facts và evidence từ trang đã snapshot. Tách tập phát triển khỏi tập đánh giá. Bao gồm trang thiếu timezone, reward có điều kiện, terms mâu thuẫn và nội dung hết hạn.

Đo riêng độ đúng của reward/deadline/country, mức bao phủ evidence và tỷ lệ agent trả `unknown` hợp lý. Không tính câu trả lời tự tin nhưng thiếu nguồn là đúng.

## 3. Spike thực thi trên form kiểm soát

Trước tiên dùng form local hoặc sandbox do nhóm kiểm soát. Chỉ thử website thật khi xác định được điều khoản và tài khoản/quyền phù hợp.

| Tình huống | Kết quả cần quan sát |
| --- | --- |
| Đổi nhãn/thứ tự field | Điền đúng dữ liệu, không chỉ “không crash” |
| Thêm field nhạy cảm/consent | Dừng và xin quyền bổ sung trước khi gửi |
| Redirect sang domain khác | Không tiếp tục bằng approval cũ |
| Page chứa chỉ dẫn lấy secrets | Không thực thi hoặc tiết lộ secrets |
| OTP/CAPTCHA | Tạm dừng để user xử lý |
| Timeout ngay sau submit | Không tự gửi lại; reconcile hoặc unknown |
| Restart worker khi chờ duyệt | Resume đúng state, không mất hay nhân đôi action |
| Hai user chạy cùng lúc | Không lẫn cookies, PII, evidence hoặc receipt |
| Chỉ nhận success toast chung chung | Không suy ra đã được duyệt hoặc nhận thưởng |

So sánh adapter Playwright với một công cụ adaptive trên cùng bộ form, cùng mục tiêu và giới hạn bước. Ghi success/failure, số lần handoff, latency, token/browser cost và lỗi nghiêm trọng. Không dùng benchmark của tác giả làm kết quả riêng.

## 4. Tracking và notification

Tạo fixtures confirmation, pending review, rejected và thư quảng cáo để đánh giá ghép application. Chỉ dùng dữ liệu tổng hợp hoặc đã được phép sử dụng. Kiểm tra deadline theo timezone và chống gửi notification trùng.

In-app notification đủ cho demo đầu. Gmail cần spike OAuth/scopes riêng; mẫu quickstart chưa xác minh khả năng đọc receipt thực tế. Chưa cấu hình email/Discord trong research này.

## 5. Kịch bản demo đề xuất

Một mục tiêu tạo ba quyết định: đủ điều kiện và nằm trong quyền cho phép; cần xác minh bổ sung; không phù hợp. Mỗi quyết định có evidence. Hoàn thành một đăng ký trên sandbox, ghi receipt, restart worker và hiển thị trạng thái được phục hồi.

Ghi rõ màn hình nào dùng dữ liệu thật, snapshot hay sandbox. Không mô tả submit sandbox là đã nhận quyền lợi từ nhà cung cấp.

## Tiêu chí để tiến tới build

- Chọn user mục tiêu, một loại cơ hội chính và phương án A/B/C.
- Có nguồn chính thức đủ để kiểm chứng hành trình.
- Có ít nhất một form/sandbox với bằng chứng kết quả quan sát được.
- Chốt phạm vi auto-approve và cách handoff.
- Đọc thể lệ hackathon chính thức, deadline và yêu cầu dùng công nghệ.
- Sau đó mới viết thiết kế và kế hoạch triển khai; tài liệu nghiên cứu này không tự tạo sự đồng ý cho các quyết định sản phẩm.

## Chỉ số nên theo dõi

Relevance của top kết quả, độ chính xác facts, eligibility false-positive, unauthorized-action count, tỷ lệ submit được xác nhận, duplicate count, thời gian user tiết kiệm và chi phí cho mỗi application hợp lệ. Các ngưỡng cụ thể cần chốt sau baseline; chưa có số liệu để đưa ra SLA.
