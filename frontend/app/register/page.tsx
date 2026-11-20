"use client";

import Link from "next/link";
import { useState } from "react";
import { api, setToken } from "@/lib/api";
import type { User } from "@/lib/types";

export default function RegisterPage() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    setPending(true);
    setError("");
    try {
      const result = await api<{ access_token: string; user: User }>("/auth/register", {
        method: "POST",
        body: JSON.stringify({ name, email, password }),
      });
      setToken(result.access_token);
      window.location.href = "/radar/profile";
    } catch (err) {
      setError(err instanceof Error ? err.message : "Không tạo được tài khoản");
      setPending(false);
    }
  }

  return (
    <main className="wrap">
      <header className="top">
        <Link className="brand" href="/">
          Job<span>Radar</span>
        </Link>
      </header>
      <form className="sheet" onSubmit={onSubmit}>
        <p className="kicker">Đăng ký</p>
        <h1 style={{ fontSize: 40 }}>Mở một radar</h1>
        <label htmlFor="name">Tên</label>
        <input id="name" autoComplete="name" value={name} onChange={(event) => setName(event.target.value)} required />
        <label htmlFor="email">Email</label>
        <input id="email" type="email" autoComplete="email" value={email} onChange={(event) => setEmail(event.target.value)} required />
        <label htmlFor="password">Mật khẩu, ít nhất 8 ký tự</label>
        <input
          id="password"
          type="password"
          autoComplete="new-password"
          minLength={8}
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          required
        />
        <p className="error">{error}</p>
        <button className="btn" type="submit" disabled={pending}>
          {pending ? "Đang tạo..." : "Tạo tài khoản"}
        </button>
        <p className="fine">
          Đã có tài khoản? <Link href="/login">Đăng nhập</Link>
        </p>
      </form>
    </main>
  );
}
