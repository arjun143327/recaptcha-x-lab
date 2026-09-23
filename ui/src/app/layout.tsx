import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

export const metadata: Metadata = {
  title: "reCAPTCHA-X-Lab | Multi-Modal CAPTCHA Robustness Dashboard",
  description:
    "Academic ML dashboard analyzing the robustness of CAPTCHA challenge-response systems across Audio, Visual, and Spatial-Reasoning modalities.",
  keywords: ["CAPTCHA", "machine learning", "robustness", "wav2vec2", "CLIP", "computer vision"],
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={inter.variable}>
      <body className="antialiased">{children}</body>
    </html>
  );
}
