# Autonomous Opportunity Hunter

Ứng dụng đang phát triển. Tài liệu nghiên cứu gốc ở [docs/README.md](docs/README.md).

## Trạng thái

Bản đầu triển khai hành trình cục bộ: tài khoản → mục tiêu → cơ hội sandbox có bằng chứng → quyết định policy → duyệt → đăng ký sandbox → theo dõi và audit. Dữ liệu mẫu là dữ liệu tổng hợp, không phải ưu đãi thật. Có xuất JSON dữ liệu riêng và xóa tài khoản cục bộ bằng mật khẩu xác nhận; thao tác xóa vô hiệu hóa mọi phiên của tài khoản. Không có đăng ký website thật, LLM, email hay Discord được bật trong bản này.

Đây chưa phải bản production. Xem [PRD](docs/product/PRD.md), [SRS](docs/product/SRS.md), [backlog](docs/product/BACKLOG.md) và [ADR](docs/architecture/ADR-001.md).

## Chạy cục bộ

Yêu cầu Python 3.12+. Trong thư mục repository:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn hunter.app:app --host 127.0.0.1 --port 8000
```

Mở ứng dụng bằng trình duyệt trong môi trường phát triển. Đăng ký tài khoản riêng với mật khẩu ít nhất 12 ký tự; không có tài khoản mặc định hoặc mật khẩu mẫu. Chọn quốc gia VN, tạo mục tiêu bằng từ khóa trong cơ hội mẫu và xem lý do policy trước khi duyệt. Chỉ sandbox có thể được submit.

Không bind ra Internet khi chưa hoàn thành hardening và TLS. Không dùng thông tin cá nhân hay mật khẩu thật để thử sandbox.

## Kiểm chứng

```sh
python -m unittest discover -s tests -v
python -m compileall -q hunter
node --check web/app.js
curl --fail http://127.0.0.1:8000/api/health
```

API tự mô tả tại `/docs`. Test sử dụng cơ sở dữ liệu tạm, không dùng dữ liệu phát triển. CI chạy các kiểm tra trên mỗi push/PR; cấu hình CI tồn tại không đồng nghĩa workflow đã chạy thành công trên GitHub.

## Phát hành

Xem [vận hành](docs/OPERATIONS.md) và [kế hoạch kiểm thử](docs/quality/TEST-PLAN.md). Tích hợp bên ngoài, migrations production, browser E2E, phục hồi backup và kiểm chứng triển khai thực tế là các cổng riêng. Không dùng điểm đánh giá của LLM để cấp quyền hành động.

Quyền riêng tư cục bộ: xem [phạm vi và kiểm thử](docs/product/PRIVACY.md). Xóa dữ liệu ứng dụng không xóa tài khoản nhà cung cấp hoặc các bản sao lưu bên ngoài.
