import type { Metadata } from "next";
import { Be_Vietnam_Pro, Source_Serif_4 } from "next/font/google";
import "./globals.css";

const sans = Be_Vietnam_Pro({
  subsets: ["latin", "vietnamese"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-sans",
});

const serif = Source_Serif_4({
  subsets: ["latin", "vietnamese"],
  weight: ["500", "600", "700"],
  variable: "--font-serif",
});

export const metadata: Metadata = {
  title: "JobRadar",
  description: "Quét việc làm public và khớp với CV của bạn.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="vi">
      <body className={`${sans.variable} ${serif.variable}`} style={{ fontFamily: "var(--font-sans), var(--sans)" }}>
        <style>{`:root { --sans: ${sans.style.fontFamily}; --serif: ${serif.style.fontFamily}; }`}</style>
        {children}
      </body>
    </html>
  );
}
