"use client";

import { useEffect, useState } from "react";
import { api, sourceLabel } from "@/lib/api";
import type { Preference } from "@/lib/types";

const SOURCES = ["vietnamworks", "topcv", "linkedin", "sample"];

export default function SettingsPage() {
  const [prefs, setPrefs] = useState<Preference | null>(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    api<Preference>("/preferences")
      .then(setPrefs)
      .catch((err: Error) => setError(err.message));
  }, []);

  function toggleSource(source: string) {
    if (!prefs) return;
    const sources = prefs.sources.includes(source) ? prefs.sources.filter((item) => item !== source) : [...prefs.sources, source];
    setPrefs({ ...prefs, sources });
  }

  async function onSave(event: React.FormEvent) {
    event.preventDefault();
    if (!prefs) return;
    setError("");
    try {
      const saved = await api<Preference>("/preferences", {
        method: "PUT",
        body: JSON.stringify({
          min_score: prefs.min_score,
          frequency: prefs.frequency,
          sources: prefs.sources,
          email_enabled: prefs.email_enabled,
        }),
      });
      setPrefs(saved);
      setMessage("Đã lưu. Lượt quét sau sẽ dùng ngưỡng và nguồn này.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Không lưu được");
    }
  }

  if (!prefs) {
    return <p className="fine">{error || "Đang tải cài đặt..."}</p>;
  }

  return (
    <form className="sheet" onSubmit={onSave}>
      <p className="kicker">Cài đặt</p>
      <h1 style={{ fontSize: 42 }}>Ngưỡng và nhịp báo</h1>
      <label htmlFor="score">Chỉ báo việc từ {prefs.min_score} điểm</label>
      <input
        id="score"
        type="range"
        min={0}
        max={100}
        value={prefs.min_score}
        onChange={(event) => setPrefs({ ...prefs, min_score: Number(event.target.value) })}
      />
      <label htmlFor="frequency">Tần suất</label>
      <select
        id="frequency"
        value={prefs.frequency}
        onChange={(event) => setPrefs({ ...prefs, frequency: event.target.value as Preference["frequency"] })}
      >
        <option value="instant">Ngay khi có tin</option>
        <option value="daily">Gom mỗi ngày</option>
        <option value="weekly">Gom mỗi tuần</option>
      </select>
      <label>Nguồn được tính điểm</label>
      {SOURCES.map((source) => (
        <label key={source} style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <input
            type="checkbox"
            checked={prefs.sources.includes(source)}
            onChange={() => toggleSource(source)}
            style={{ width: 18 }}
          />
          {sourceLabel[source]}
        </label>
      ))}
      <label style={{ display: "flex", gap: 8, alignItems: "center" }}>
        <input
          type="checkbox"
          checked={prefs.email_enabled}
          onChange={(event) => setPrefs({ ...prefs, email_enabled: event.target.checked })}
          style={{ width: 18 }}
        />
        Gửi email
      </label>
      <p className="fine">
        TopCV và LinkedIn thường chặn request tự động. Lượt quét ghi blocked và không vượt captcha. Bật tin mẫu nếu muốn
        xem matching khi nguồn thật trống. Chưa có Resend API key thì thư nằm trong hộp thư trên bản tin.
      </p>
      <p className="fine">{message}</p>
      <p className="error">{error}</p>
      <button className="btn" type="submit">
        Lưu cài đặt
      </button>
    </form>
  );
}
