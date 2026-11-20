"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { api, clearToken } from "@/lib/api";
import type { User } from "@/lib/types";

const LINKS = [
  { href: "/radar", label: "Bản tin" },
  { href: "/radar/profile", label: "Hồ sơ" },
  { href: "/radar/settings", label: "Cài đặt" },
];

export default function RadarLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    api<User>("/auth/me")
      .then(setUser)
      .catch(() => setUser(null));
  }, []);

  return (
    <main className="wrap">
      <header className="top">
        <Link className="brand" href="/radar">
          Job<span>Radar</span>
        </Link>
        <nav className="nav">
          {LINKS.map((link) => (
            <Link key={link.href} href={link.href} aria-current={pathname === link.href ? "page" : undefined}>
              {link.label}
            </Link>
          ))}
          <span className="fine">{user?.name}</span>
          <button
            className="text-btn"
            type="button"
            onClick={() => {
              clearToken();
              window.location.href = "/";
            }}
          >
            Thoát
          </button>
        </nav>
      </header>
      {children}
    </main>
  );
}
