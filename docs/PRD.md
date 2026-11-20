# Product Requirements Document (PRD)

**Project:** JobRadar - Hệ thống Radar Tìm Việc theo CV  
**Author:** Ethan  
**Date:** 20/11/2026  
**Version:** 1.0

## 1. Tổng quan

JobRadar là hệ thống tự động theo dõi và tìm kiếm cơ hội việc làm phù hợp dựa trên CV của người dùng. Hệ thống quét định kỳ các nền tảng tuyển dụng, so khớp với hồ sơ người dùng và gửi thông báo khi có job mới phù hợp.

Mục tiêu: giúp người tìm việc không bỏ lỡ cơ hội, giảm thời gian tìm kiếm thủ công.

## 2. Mục tiêu và chỉ số thành công

- Người dùng nhận được ít nhất 5 job phù hợp mỗi tuần.
- Tỷ lệ job match có score >= 70% đạt trên 60%.
- Thời gian từ lúc job được đăng đến lúc user nhận thông báo dưới 6 giờ.
- Tỷ lệ người dùng mở notification trên 40%.

## 3. Người dùng mục tiêu

- Người đi làm muốn chuyển việc.
- Sinh viên mới tốt nghiệp.
- Freelancer tìm dự án dài hạn.
- Người ở Hà Nội và các thành phố lớn tại Việt Nam.

## 4. Tính năng chính (MVP)

### 4.1. Quản lý hồ sơ

- Upload CV (PDF).
- Hệ thống tự động extract: kỹ năng, kinh nghiệm, vị trí mong muốn, mức lương.
- Cho phép chỉnh sửa thông tin đã extract.

### 4.2. Tìm kiếm và theo dõi job

Quét định kỳ các nguồn:

- VietnamWorks
- TopCV
- LinkedIn Jobs
- Indeed
- Facebook Groups tuyển dụng (một số group lớn)

Job mới được lưu vào database.

### 4.3. Matching engine

- So khớp CV với job description.
- Tính điểm phù hợp (0-100).
- Lọc theo kỹ năng, kinh nghiệm, địa điểm, mức lương.

### 4.4. Thông báo

- Gửi email hoặc Telegram khi có job mới có điểm >= ngưỡng.
- Cho phép user điều chỉnh ngưỡng điểm và tần suất nhận thông báo.

### 4.5. Dashboard

- Danh sách job đã match.
- Trạng thái: đã xem, đã lưu, đã apply.
- Lịch sử matching.

## 5. Luồng người dùng

1. Đăng ký hoặc đăng nhập.
2. Upload CV.
3. Hệ thống extract thông tin, user xác nhận hoặc chỉnh sửa.
4. Hệ thống bắt đầu quét job định kỳ.
5. Khi có job phù hợp, gửi notification.
6. User xem chi tiết job, rồi lưu hoặc apply.
7. User có thể chỉnh preference: ngưỡng điểm, nguồn job, tần suất.

## 6. Yêu cầu kỹ thuật

| Hạng mục | Lựa chọn |
| --- | --- |
| Backend | Python (FastAPI) |
| Crawler | Playwright hoặc Scrapy |
| Database | Supabase (PostgreSQL) |
| Matching | Rule-based + embedding (tùy chọn) |
| Notification | Email (Resend) hoặc Telegram Bot |
| Frontend | Next.js hoặc Flutter (Web) |
| Storage | Supabase Storage (lưu CV) |

## 7. Phạm vi MVP

Trong phạm vi:

- Upload và extract CV.
- Crawl 3 nguồn chính: VietnamWorks, TopCV, LinkedIn.
- Matching cơ bản.
- Notification qua email.
- Dashboard đơn giản.

Ngoài phạm vi (giai đoạn sau):

- Apply tự động.
- Phân tích thị trường lương.
- AI viết cover letter.
- Mobile app native.

## 8. Rủi ro và giải pháp

| Rủi ro | Giải pháp |
| --- | --- |
| Nguồn job thay đổi cấu trúc | Thiết kế crawler module hóa, dễ cập nhật |
| Trùng lặp job | Dùng hash của title + company + location để deduplicate |
| Spam notification | Cho phép user đặt ngưỡng điểm và tần suất |
| Pháp lý scraping | Chỉ crawl dữ liệu public, tôn trọng robots.txt |

## 9. Kế hoạch triển khai

| Tuần | Việc |
| --- | --- |
| Tuần 1 | Schema, auth, upload CV, extract |
| Tuần 2 | Crawler cho 2 nguồn chính, matching cơ bản |
| Tuần 3 | Notification, dashboard |
| Tuần 4 | Test với 10-15 người dùng thật, tinh chỉnh |

## 10. Tiêu chí hoàn thành MVP

- Người dùng upload CV và nhận được ít nhất 3 job phù hợp trong 48 giờ.
- Hệ thống chạy ổn định 7 ngày liên tục.
- Có ít nhất 10 người dùng test thực tế.
