"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { api, sourceLabel, statusLabel } from "@/lib/api";
import type { Match } from "@/lib/types";

const BARS = [
  ["skills", "Kỹ năng", 40],
  ["experience", "Kinh nghiệm", 20],
  ["title", "Vị trí", 15],
  ["location", "Địa điểm", 15],
  ["salary", "Lương", 10],
] as const;

export default function JobPage() {
  const params = useParams<{ id: string }>();
  const [match, setMatch] = useState<Match | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api<Match>(`/matches/${params.id}`)
      .then(setMatch)
      .catch((err: Error) => setError(err.message));
  }, [params.id]);

  async function setStatus(status: Match["status"]) {
    const updated = await api<Match>(`/matches/${params.id}`, {
      method: "PATCH",
      body: JSON.stringify({ status }),
    });
    setMatch(updated);
  }

  if (!match) return <p className="fine">{error || "Đang mở tin..."}</p>;
  const sample = match.job.source === "sample" || match.job.url.includes("example.com");

  return (
    <section className="detail">
      <article className="prose card">
        <p className="kicker">{sourceLabel[match.job.source] || match.job.source}</p>
        <h1>{match.job.title}</h1>
        <p className="lead">
          {match.job.company} · {match.job.location || "Chưa rõ nơi"} · {match.job.salary_text || "Lương chưa rõ"}
        </p>
        <p>{match.job.description || "Tin này chưa có mô tả đầy đủ. Điểm đang dựa trên tiêu đề, nơi làm và lương."}</p>
        <div className="actions">
          <button className="btn-ghost" type="button" onClick={() => setStatus("saved")}>
            Lưu
          </button>
          <button className="btn" type="button" onClick={() => setStatus("applied")}>
            Đánh dấu đã apply
          </button>
          {sample ? null : (
            <a className="btn-ghost" href={match.job.url} target="_blank" rel="noreferrer">
              Mở tin gốc
            </a>
          )}
        </div>
        {sample ? <p className="fine">Tin mẫu không có trang tuyển dụng thật.</p> : null}
        <p className="fine">Trạng thái hiện tại: {statusLabel[match.status]}</p>
      </article>
      <aside className="side">
        <h2>{match.score}</h2>
        <p className="fine">điểm khớp</p>
        <div className="bars">
          {BARS.map(([key, label, max]) => {
            const value = Number(match.breakdown[key] || 0);
            return (
              <div className="bar" key={key}>
                <span>{label}</span>
                <div className="track">
                  <span style={{ width: `${Math.min(100, (value / max) * 100)}%` }} />
                </div>
                <b>{value}</b>
              </div>
            );
          })}
        </div>
        <ul className="reasons">
          {(match.breakdown.reasons || []).map((reason) => (
            <li key={reason}>{reason}</li>
          ))}
        </ul>
        <Link href="/radar">Quay lại bản tin</Link>
      </aside>
    </section>
  );
}
