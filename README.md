# JobRadar

Hệ thống radar tìm việc theo CV. JobRadar quét định kỳ các nền tảng tuyển dụng, so khớp với hồ sơ người dùng và gửi thông báo khi có job mới đủ điểm.

Mục tiêu: người tìm việc không bỏ lỡ cơ hội, và bớt thời gian tìm thủ công.

PRD đầy đủ: [docs/PRD.md](docs/PRD.md) (v1.0, 20/11/2026).

## Người dùng

- Người đi làm muốn chuyển việc
- Sinh viên mới tốt nghiệp
- Freelancer tìm dự án dài hạn
- Người ở Hà Nội và các thành phố lớn tại Việt Nam

## MVP

Trong phạm vi:

- Upload CV (PDF), extract kỹ năng, kinh nghiệm, vị trí mong muốn, mức lương, rồi cho user sửa lại
- Crawl 3 nguồn: VietnamWorks, TopCV, LinkedIn Jobs
- Matching cơ bản, điểm 0-100, lọc theo kỹ năng, kinh nghiệm, địa điểm, mức lương
- Email khi job đạt ngưỡng điểm. User chỉnh ngưỡng và tần suất
- Dashboard: job đã match, trạng thái đã xem / đã lưu / đã apply, lịch sử matching

Ngoài phạm vi, để giai đoạn sau: apply tự động, phân tích thị trường lương, AI viết cover letter, mobile app native. Indeed và Facebook Groups tuyển dụng cũng nằm ngoài 3 nguồn của MVP.

## Luồng

1. Đăng ký hoặc đăng nhập
2. Upload CV
3. Hệ thống extract, user xác nhận hoặc chỉnh sửa
4. Hệ thống quét job định kỳ
5. Job đủ điểm thì gửi email
6. User xem chi tiết, lưu hoặc apply
7. User chỉnh preference: ngưỡng điểm, nguồn job, tần suất

## Chỉ số thành công

- Ít nhất 5 job phù hợp mỗi user mỗi tuần
- Trên 60% job match có score >= 70%
- Từ lúc job được đăng đến lúc user nhận thông báo: dưới 6 giờ
- Tỷ lệ mở notification trên 40%

MVP được coi là xong khi:

- User upload CV và nhận ít nhất 3 job phù hợp trong 48 giờ
- Hệ thống chạy ổn định 7 ngày liên tục
- Có ít nhất 10 người dùng test thực tế

## Stack

| Hạng mục | Lựa chọn |
| --- | --- |
| Backend | Python, FastAPI |
| Crawler | Playwright hoặc Scrapy, module hóa theo từng nguồn |
| Database | Supabase (PostgreSQL) |
| Storage | Supabase Storage cho file CV |
| Matching | Rule-based, embedding là tùy chọn |
| Notification | Email qua Resend. Telegram Bot để sau |
| Frontend | Next.js hoặc Flutter Web |

Dedup job bằng hash của title + company + location. Crawler chỉ lấy dữ liệu public và tôn trọng `robots.txt`.

## Kế hoạch 4 tuần

| Tuần | Việc |
| --- | --- |
| 1 | Schema, auth, upload CV, extract |
| 2 | Crawler 2 nguồn chính, matching cơ bản |
| 3 | Notification, dashboard |
| 4 | Test với 10-15 người dùng thật, tinh chỉnh |

## Trạng thái

Repo mới khởi tạo. Chưa có code. Tài liệu sản phẩm nằm ở `docs/PRD.md`.
