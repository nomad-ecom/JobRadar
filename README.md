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

## Stack đang chạy

| Hạng mục | Lựa chọn |
| --- | --- |
| Backend | Python, FastAPI, `backend/` |
| Frontend | Next.js, `frontend/` |
| Database | SQLite khi dev. Postgres qua `DATABASE_URL`, kể cả Supabase |
| CV | Đĩa local, hoặc Supabase Storage khi có key |
| Crawler | Một module mỗi nguồn. HTTP đọc HTML public. Playwright là lần thử lại, bật bằng biến môi trường |
| Matching | Rule-based, điểm 0-100 |
| Email | Resend. Không có key thì thư nằm trong hộp thư trên bản tin |

Dedup bằng hash của title + company + location, không phân biệt hoa thường và dấu. Crawler chỉ đọc trang public, tôn trọng `robots.txt`, và dừng khi gặp trang chặn. Không vượt captcha.

VietnamWorks: đọc các tin nổi bật nhúng trong HTML public, không phải toàn bộ kết quả tìm kiếm. TopCV và LinkedIn thường trả 403. Trạng thái đó hiện trong lượt quét. Nguồn `sample` là tin giả để chạy thử matching, bật mặc định lúc dev, tắt bằng `JOBRADAR_SAMPLE_SOURCE=false`.

## Chạy local

```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/uvicorn app.main:app --reload --port 8000
```

Terminal khác:

```bash
cd frontend
npm install
npm run dev
```

Mở http://localhost:3000. Đăng ký, nhập hồ sơ hoặc upload PDF, rồi bấm Quét ngay.

Postgres thay cho SQLite:

```bash
docker compose up --build
```

API trong Docker dùng `postgresql+psycopg://jobradar:jobradar@db:5432/jobradar`. Biến môi trường nằm ở `.env.example`.

Quét một lần không qua web:

```bash
cd backend && .venv/bin/python -m app
```

Test:

```bash
cd backend && .venv/bin/pytest
```

Scheduler trong process API chạy sau mỗi `JOBRADAR_CRAWL_INTERVAL_MINUTES` (mặc định 180). Lần đầu không quét ngay lúc bật server.

## Kế hoạch 4 tuần

| Tuần | Việc |
| --- | --- |
| 1 | Schema, auth, upload CV, extract |
| 2 | Crawler 2 nguồn chính, matching cơ bản |
| 3 | Notification, dashboard |
| 4 | Test với 10-15 người dùng thật, tinh chỉnh |
