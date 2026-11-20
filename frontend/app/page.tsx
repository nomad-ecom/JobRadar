import Link from "next/link";

export default function HomePage() {
  return (
    <main className="wrap">
      <header className="top">
        <Link className="brand" href="/">
          Job<span>Radar</span>
        </Link>
        <nav className="nav">
          <Link href="/login">Đăng nhập</Link>
          <Link className="btn" href="/register">
            Tạo tài khoản
          </Link>
        </nav>
      </header>
      <section className="hero">
        <div>
          <p className="kicker">Bản tin việc làm theo CV</p>
          <h1>Việc mới tới trước khi bạn mở thêm một tab.</h1>
          <p className="lead">
            Tải CV một lần. JobRadar đọc kỹ năng, kinh nghiệm, nơi làm và mức lương, rồi quét VietnamWorks, TopCV và
            LinkedIn. Tin đủ điểm thì có email.
          </p>
          <div className="actions">
            <Link className="btn" href="/register">
              Bắt đầu với CV
            </Link>
            <Link className="btn-ghost" href="/radar">
              Vào bản tin
            </Link>
          </div>
        </div>
        <div className="radar" aria-hidden="true">
          <i className="blip" />
          <i className="blip" />
          <i className="blip" />
        </div>
      </section>
      <section className="steps">
        <article className="step">
          <b>01</b>
          <p>Upload PDF. Hệ thống tách vị trí, kỹ năng, số năm và mức lương. Bạn sửa lại trước khi dùng.</p>
        </article>
        <article className="step">
          <b>02</b>
          <p>Mỗi lượt quét lưu tin mới, bỏ tin trùng theo tên việc, công ty và địa điểm, rồi chấm điểm 0-100.</p>
        </article>
        <article className="step">
          <b>03</b>
          <p>Email gửi khi điểm vượt ngưỡng bạn chọn. Trên bản tin, đánh dấu đã xem, đã lưu hoặc đã apply.</p>
        </article>
      </section>
    </main>
  );
}
