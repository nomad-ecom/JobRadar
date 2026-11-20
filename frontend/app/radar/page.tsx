"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { API_URL, api, formatWhen, sourceLabel, statusLabel } from "@/lib/api";
import type { CrawlRun, Match, Notice, Stats } from "@/lib/types";

const FILTERS = [
  { id: "all", label: "Tất cả" },
  { id: "high", label: "Từ 70 điểm" },
  { id: "new", label: "Mới" },
  { id: "saved", label: "Đã lưu" },
  { id: "applied", label: "Đã apply" },
] as const;

type FilterId = (typeof FILTERS)[number]["id"];

export default function RadarPage() {
  const [matches, setMatches] = useState<Match[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [runs, setRuns] = useState<CrawlRun[]>([]);
  const [notes, setNotes] = useState<Notice[]>([]);
  const [filter, setFilter] = useState<FilterId>("all");
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);
  const [openNote, setOpenNote] = useState<string | null>(null);

  async function load(next = filter) {
    const query = next === "high" ? "?min_score=70" : next === "all" ? "" : `?status=${next}`;
    const [matchRows, statRow, runRows, noteRows] = await Promise.all([
      api<Match[]>(`/matches${query}`),
      api<Stats>("/matches/stats"),
      api<CrawlRun[]>("/crawl/runs"),
      api<Notice[]>("/notifications"),
    ]);
    setMatches(matchRows);
    setStats(statRow);
    setRuns(runRows);
    setNotes(noteRows);
  }

  useEffect(() => {
    load(filter).catch((err: Error) => setError(err.message));
    // load depends on filter via the argument, not the closure.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filter]);

  async function scan() {
    setPending(true);
    setError("");
    try {
      await api<CrawlRun[]>("/crawl", { method: "POST" });
      await load(filter);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Quét lỗi");
    } finally {
      setPending(false);
    }
  }

  return (
    <section className="app-grid">
      <div>
        <div className="stats">
          <div className="stat">
            <span>Việc đã khớp</span>
            <strong>{stats?.total ?? "-"}</strong>
          </div>
          <div className="stat">
            <span>Từ 70 điểm</span>
            <strong>{stats?.high ?? "-"}</strong>
          </div>
          <div className="stat">
            <span>Chưa xem</span>
            <strong>{stats?.new ?? "-"}</strong>
          </div>
          <div className="stat">
            <span>Đã báo</span>
            <strong>{stats?.notified ?? "-"}</strong>
          </div>
        </div>
        <div className="filters">
          {FILTERS.map((item) => (
            <button key={item.id} className="chip" type="button" aria-pressed={filter === item.id} onClick={() => setFilter(item.id)}>
              {item.label}
            </button>
          ))}
        </div>
        <p className="error">{error}</p>
        <div className="jobs">
          {matches.length === 0 ? (
            <div className="card empty">
              <h2>Chưa có việc trong bộ lọc này</h2>
              <p className="fine">Hãy điền hồ sơ rồi bấm Quét ngay. Tin mẫu giúp xem luồng khi nguồn thật bị chặn.</p>
              <Link className="btn" href="/radar/profile">
                Mở hồ sơ
              </Link>
            </div>
          ) : (
            matches.map((match) => (
              <Link className="job" key={match.id} href={`/radar/jobs/${match.id}`}>
                <div className={match.score >= 70 ? "score high" : "score"}>
                  {match.score}
                  <small>điểm</small>
                </div>
                <div>
                  <h2>{match.job.title}</h2>
                  <div className="meta">
                    {match.job.company} · {match.job.location || "Chưa rõ nơi"} · {match.job.salary_text || "Lương chưa rõ"}
                  </div>
                  <div className="tags">
                    <span className={match.job.source === "sample" ? "stamp sample" : "stamp"}>
                      {sourceLabel[match.job.source] || match.job.source}
                    </span>
                    <span className="tag">{statusLabel[match.status]}</span>
                  </div>
                </div>
              </Link>
            ))
          )}
        </div>
      </div>
      <aside className="side">
        <h2>Lượt quét</h2>
        <p className="fine">Scheduler chạy theo chu kỳ. Bấm bên dưới nếu muốn quét ngay.</p>
        <button className="btn" type="button" onClick={scan} disabled={pending}>
          {pending ? "Đang quét..." : "Quét ngay"}
        </button>
        {runs.slice(0, 6).map((run) => (
          <div className="run" key={run.id}>
            <b>{sourceLabel[run.source] || run.source}</b> · {run.status} · mới {run.jobs_new}
            <div className="note">{run.message}</div>
          </div>
        ))}
        <h2 style={{ marginTop: 18 }}>Hộp thư</h2>
        {notes.length === 0 ? <p className="fine">Chưa có thông báo. Khi chưa cấu hình Resend, thư nằm ở đây.</p> : null}
        {notes.map((note) => (
          <button
            className="run"
            key={note.id}
            type="button"
            onClick={() => {
              setOpenNote(openNote === note.id ? null : note.id);
              if (!note.opened_at) fetch(`${API_URL}/notifications/${note.id}/open.gif`);
            }}
            style={{ display: "block", width: "100%", textAlign: "left", background: "transparent" }}
          >
            <b>{note.subject}</b>
            <div className="note">
              {note.status} · {formatWhen(note.created_at)}
              {openNote === note.id ? `\n${note.body}` : ""}
            </div>
          </button>
        ))}
      </aside>
    </section>
  );
}
