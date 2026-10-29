# Project và công cụ tham khảo

Các khả năng bên dưới được đọc từ tài liệu project ngày 29/10/2026; không phải kết quả benchmark. Chỉ chọn một vài dependency cho MVP, không cài toàn bộ danh sách.

## Agent và orchestration

| Project | Điều đáng tham khảo | Đề xuất sử dụng và trade-off |
| --- | --- | --- |
| [OpenAI Agents SDK JS/TS](https://github.com/openai/openai-agents-js) | Tools, guardrails, human-in-the-loop, sessions, tracing | Ứng viên cho runtime TypeScript; tracing không thay thế business audit và DB trạng thái |
| [OpenAI Agents SDK Python](https://github.com/openai/openai-agents-python) | Cùng các primitives trên, examples và tools | Ứng viên nếu backend Python; không cần dùng cả SDK Python và JS |
| [LangGraph](https://github.com/langchain-ai/langgraph) | Durable execution, memory, interrupts/human-in-the-loop | Hữu ích với workflow nhiều vòng; thêm mô hình state/checkpoint cần học và vận hành |
| [Inngest](https://github.com/inngest/inngest) | Event/cron triggers, steps, retries, background workflows | Ứng viên cho reminders và jobs; retry không làm submit bên ngoài trở nên exactly-once; server/CLI có điều khoản license riêng cần đọc trước khi self-host |
| [Codex](https://github.com/openai/codex) | Coding agent, CLI/IDE/cloud workflows | Tham khảo để phát triển connector và test; không mặc định là browser automation runtime hoặc yêu cầu bắt buộc của hackathon |

## Browser automation

| Project | Điều đáng tham khảo | Trade-off và cách dùng |
| --- | --- | --- |
| [Playwright](https://github.com/microsoft/playwright) | Role/label locators, auto-wait, browser contexts, storage state và traces | Nền tảng adapter có kiểm soát; cần tự xử lý thay đổi form, auth và xác nhận kết quả |
| [Playwright MCP](https://github.com/microsoft/playwright-mcp) | Agent thao tác qua accessibility snapshots | Hợp với khám phá trang; tài liệu ghi origin allow/block filters không phải security boundary và không kiểm soát redirects |
| [Stagehand](https://github.com/browserbase/stagehand) | `observe`, `act`, `extract`; phối hợp natural language và browser operations | Ứng viên cho bước không ổn định; khả năng self-healing là claim tài liệu, chưa kiểm chứng ở form mục tiêu |
| [Browser Use](https://github.com/browser-use/browser-use) | Browser agent local/cloud và lựa chọn model | Hợp cho spike browser agent rộng; cần đo chi phí, số bước, lỗi và session isolation; không lấy benchmark marketing làm kết quả dự án |

**Lựa chọn sơ bộ:** bắt đầu bằng Playwright adapter cho 1–2 website được phép. Chỉ thử Stagehand hoặc Browser Use trên bộ form kiểm soát nếu adapter tĩnh không đáp ứng. Không trộn cả ba browser frameworks từ đầu.

Mỗi user có context/session riêng; storage state chứa quyền truy cập tài khoản và phải được bảo vệ như credential. Persistent profile không được dùng chung tùy tiện giữa user/jobs. Ẩn dữ liệu nhạy cảm trong trace, screenshot và logs.

## Crawling và extraction

| Project | Điều đáng tham khảo | Khi nên chọn |
| --- | --- | --- |
| [Crawlee](https://github.com/apify/crawlee) | Crawling/scraping và tích hợp browser trong hệ JS | Khi cần hàng đợi crawl có cấu trúc; chỉ dùng trên nguồn được phép, không cần các khả năng né bot cho MVP |
| [Crawl4AI](https://github.com/unclecode/crawl4ai) | Chuyển web thành Markdown, extraction và local/hosted workflows | Khi chọn Python hoặc muốn thử nội dung LLM-ready; vẫn phải đo mất nội dung quan trọng khi chuyển đổi |
| [Firecrawl](https://github.com/firecrawl/firecrawl) | Search, scrape, crawl, extraction và hosted API | Khi muốn giảm công vận hành; cần kiểm tra coverage, quota, giá và license từng phần trước khi chọn |

Trang tĩnh ít nguồn có thể chỉ cần HTTP + HTML parser. Browser dành cho trang cần JavaScript; không mở browser cho mọi URL nếu không cần.

## Theo dõi và thông báo

[Gmail quickstart chính thức](https://github.com/googleworkspace/python-samples/blob/main/gmail/quickstart/quickstart.py) minh họa OAuth, refresh token và scope `gmail.readonly`; ví dụ thực hiện liệt kê labels. Nó **không chứng minh** parsing confirmation email, mail sending, webhook nhận mail hoặc OAuth production đã sẵn sàng.

Nếu triển khai: thiết kế consent/scopes riêng cho đọc và gửi; ghép email với application dựa trên sender, program và receipt, không chỉ từ khóa “congratulations”. Token không được commit hoặc đưa vào prompt.

Discord webhook là phương án cần nghiên cứu tiếp. URL tài liệu raw thử trong đợt này trả 404 nên không dùng làm bằng chứng, không giả định endpoint hoặc cơ chế bảo mật từ URL đó.

## Trước khi thêm dependency

- Đọc license file và điều khoản hosted service ở phiên bản định dùng; README badge chưa đủ cho quyết định phân phối.
- Chốt runtime, pin version và lockfile lúc triển khai. Không sao chép các lệnh `latest` vào production plan.
- Kiểm tra nguồn dữ liệu gửi tới model/provider, yêu cầu API keys, browser binaries và tài nguyên worker.
- Đo chất lượng trên cùng tập form; chọn công cụ từ kết quả thực tế thay vì số sao GitHub.
