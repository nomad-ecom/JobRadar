"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Profile } from "@/lib/types";

const EMPTY: Profile = {
  desired_title: "",
  summary: "",
  skills: [],
  experience_years: null,
  locations: [],
  salary_min: null,
  salary_max: null,
  salary_currency: "VND",
  cv_path: "",
  updated_at: null,
};

export default function ProfilePage() {
  const [profile, setProfile] = useState<Profile>(EMPTY);
  const [skills, setSkills] = useState("");
  const [locations, setLocations] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);

  useEffect(() => {
    api<Profile>("/profile")
      .then((row) => {
        setProfile(row);
        setSkills(row.skills.join(", "));
        setLocations(row.locations.join(", "));
      })
      .catch(() => setProfile(EMPTY));
  }, []);

  function applyProfile(row: Profile, note: string) {
    setProfile(row);
    setSkills(row.skills.join(", "));
    setLocations(row.locations.join(", "));
    setMessage(note);
  }

  async function onUpload(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    setPending(true);
    setError("");
    const body = new FormData();
    body.append("file", file);
    try {
      const row = await api<Profile>("/profile/cv", { method: "POST", body });
      applyProfile(row, "Đã đọc PDF. Kiểm tra lại các trường rồi lưu.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Không đọc được CV");
    } finally {
      setPending(false);
    }
  }

  async function onSave(event: React.FormEvent) {
    event.preventDefault();
    setPending(true);
    setError("");
    try {
      const row = await api<Profile>("/profile", {
        method: "PUT",
        body: JSON.stringify({
          desired_title: profile.desired_title,
          summary: profile.summary,
          skills: skills.split(",").map((item) => item.trim()).filter(Boolean),
          experience_years: profile.experience_years,
          locations: locations.split(",").map((item) => item.trim()).filter(Boolean),
          salary_min: profile.salary_min,
          salary_max: profile.salary_max,
          salary_currency: profile.salary_currency || "VND",
        }),
      });
      applyProfile(row, "Đã lưu hồ sơ. Quay lại bản tin và bấm Quét ngay.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Không lưu được");
    } finally {
      setPending(false);
    }
  }

  return (
    <form className="sheet" onSubmit={onSave} style={{ width: "min(720px, 100%)" }}>
      <p className="kicker">Hồ sơ</p>
      <h1 style={{ fontSize: 42 }}>CV đang dùng để so</h1>
      <label htmlFor="cv">Upload PDF, tối đa 5MB</label>
      <input id="cv" type="file" accept="application/pdf,.pdf" onChange={onUpload} />
      <label htmlFor="title">Vị trí mong muốn</label>
      <input
        id="title"
        value={profile.desired_title}
        onChange={(event) => setProfile({ ...profile, desired_title: event.target.value })}
      />
      <label htmlFor="summary">Tóm tắt</label>
      <textarea
        id="summary"
        value={profile.summary}
        onChange={(event) => setProfile({ ...profile, summary: event.target.value })}
      />
      <label htmlFor="skills">Kỹ năng, cách nhau bằng dấu phẩy</label>
      <input id="skills" value={skills} onChange={(event) => setSkills(event.target.value)} />
      <div className="row">
        <div>
          <label htmlFor="years">Số năm kinh nghiệm</label>
          <input
            id="years"
            type="number"
            min={0}
            step="0.5"
            value={profile.experience_years ?? ""}
            onChange={(event) =>
              setProfile({ ...profile, experience_years: event.target.value === "" ? null : Number(event.target.value) })
            }
          />
        </div>
        <div>
          <label htmlFor="places">Địa điểm</label>
          <input id="places" value={locations} onChange={(event) => setLocations(event.target.value)} />
        </div>
      </div>
      <div className="row">
        <div>
          <label htmlFor="min">Lương tối thiểu (VND)</label>
          <input
            id="min"
            type="number"
            min={0}
            value={profile.salary_min ?? ""}
            onChange={(event) =>
              setProfile({ ...profile, salary_min: event.target.value === "" ? null : Number(event.target.value) })
            }
          />
        </div>
        <div>
          <label htmlFor="max">Lương tối đa (VND)</label>
          <input
            id="max"
            type="number"
            min={0}
            value={profile.salary_max ?? ""}
            onChange={(event) =>
              setProfile({ ...profile, salary_max: event.target.value === "" ? null : Number(event.target.value) })
            }
          />
        </div>
      </div>
      <p className="fine">{message}</p>
      <p className="error">{error}</p>
      <button className="btn" type="submit" disabled={pending}>
        {pending ? "Đang lưu..." : "Lưu hồ sơ"}
      </button>
    </form>
  );
}
