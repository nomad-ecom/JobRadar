"use client";

import Link from "next/link";
import { useState } from "react";
import { api, setToken } from "@/lib/api";
import type { User } from "@/lib/types";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    setPending(true);
    setError("");
    try {
      const result = await api<{ access_token: string; user: User }>("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      setToken(result.access_token);
      window.location.href = "/radar";
    } catch (err) {
      setError(err instanceof Error ? err.message : "Không đăng nhập được");
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
        <p className="kicker">Đăng nhập</p>
        <h1 style={{ fontSize: 40 }}>Vào bản tin của bạn</h1>
        <label htmlFor="email">Email</label>
        <input id="email" type="email" autoComplete="email" value={email} onChange={(event) => setEmail(event.target.value)} required />
        <label htmlFor="password">Mật khẩu</label>
        <input id="password" type="password" autoComplete="current-password" value={password} onChange={(event) => setPassword(event.target.value)} required />
        <p className="error">{error}</p>
        <button className="btn" type="submit" disabled={pending}>
          {pending ? "Đang vào..." : "Đăng nhập"}
        </button>
        <p className="fine">
          Chưa có tài khoản? <Link href="/register">Đăng ký</Link>
        </p>
      </form>
    </main>
  );
}
