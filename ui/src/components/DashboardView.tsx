"use client";

import { useState } from "react";
import { PRECOMPUTED_METRICS } from "@/lib/metrics";
import type { ActiveView } from "@/app/page";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import {
  Bell,
  Settings as SettingsIcon,
  Search,
  Sparkles,
  ArrowUpRight,
  TrendingUp,
  TrendingDown,
  ChevronDown,
  Eye,
  Mic,
  Puzzle,
  Network,
  ShieldAlert,
} from "lucide-react";

interface DashboardViewProps {
  onNavigate?: (view: ActiveView) => void;
}

const m = PRECOMPUTED_METRICS;

// Robustness curve data matching the reference image's wavy graph
const PERFORMANCE_DATA_SETS = {
  "1D": [
    { label: "Jan", visual: 85, audio: 0, puzzle: 25, overall: 48, raw: "Clean Baseline" },
    { label: "Feb", visual: 83, audio: 0, puzzle: 24, overall: 46, raw: "White Noise 2dB" },
    { label: "Mar", visual: 81, audio: 0, puzzle: 23, overall: 44, raw: "Gaussian Blur σ=1" },
    { label: "Apr", visual: 78, audio: 0, puzzle: 22, overall: 42, raw: "Contrast Shift" },
    { label: "May", visual: 74, audio: 0, puzzle: 20, overall: 38, raw: "Pitch Jitter" },
    { label: "Jun", visual: 68, audio: 0, puzzle: 18, overall: 35, raw: "Gaussian Blur σ=2" },
    { label: "Jul", visual: 72, audio: 0, puzzle: 20, overall: 37, raw: "Speckle Noise" },
    { label: "Aug", visual: 65, audio: 0, puzzle: 15, overall: 32, raw: "High Distortion" },
    { label: "Sep", visual: 70, audio: 0, puzzle: 18, overall: 34, raw: "Partial Occlusion" },
    { label: "Oct", visual: 62, audio: 0, puzzle: 14, overall: 30, raw: "Adversarial Grid" },
    { label: "Nov", visual: 58, audio: 0, puzzle: 12, overall: 28, raw: "Multi-Perturbation" },
    { label: "Dec", visual: 55, audio: 0, puzzle: 10, overall: 26, raw: "Extreme Noise" },
  ],
  "1W": [
    { label: "Mon", visual: 88, audio: 10, puzzle: 30, overall: 52 },
    { label: "Tue", visual: 85, audio: 5, puzzle: 28, overall: 48 },
    { label: "Wed", visual: 82, audio: 0, puzzle: 25, overall: 44 },
    { label: "Thu", visual: 80, audio: 0, puzzle: 22, overall: 42 },
    { label: "Fri", visual: 75, audio: 0, puzzle: 20, overall: 38 },
    { label: "Sat", visual: 70, audio: 0, puzzle: 18, overall: 35 },
    { label: "Sun", visual: 68, audio: 0, puzzle: 16, overall: 33 },
  ],
  "1M": [
    { label: "W1", visual: 90, audio: 10, puzzle: 32, overall: 54 },
    { label: "W2", visual: 85, audio: 5, puzzle: 28, overall: 48 },
    { label: "W3", visual: 79, audio: 0, puzzle: 24, overall: 42 },
    { label: "W4", visual: 68, audio: 0, puzzle: 19, overall: 35 },
  ],
  "6M": [
    { label: "Jul", visual: 88, audio: 0, puzzle: 28, overall: 48 },
    { label: "Aug", visual: 84, audio: 0, puzzle: 25, overall: 45 },
    { label: "Sep", visual: 80, audio: 0, puzzle: 22, overall: 42 },
    { label: "Oct", visual: 75, audio: 0, puzzle: 19, overall: 38 },
    { label: "Nov", visual: 71, audio: 0, puzzle: 17, overall: 35 },
    { label: "Dec", visual: 68, audio: 0, puzzle: 15, overall: 33 },
  ],
  "1Y": [
    { label: "Jan", visual: 88, audio: 0, puzzle: 28, overall: 48 },
    { label: "Feb", visual: 86, audio: 0, puzzle: 26, overall: 46 },
    { label: "Mar", visual: 84, audio: 0, puzzle: 24, overall: 44 },
    { label: "Apr", visual: 80, audio: 0, puzzle: 22, overall: 42 },
    { label: "May", visual: 75, audio: 0, puzzle: 20, overall: 38 },
    { label: "Jun", visual: 68, audio: 0, puzzle: 18, overall: 35 },
    { label: "Jul", visual: 72, audio: 0, puzzle: 21, overall: 38 },
    { label: "Aug", visual: 66, audio: 0, puzzle: 16, overall: 33 },
    { label: "Sep", visual: 69, audio: 0, puzzle: 19, overall: 35 },
    { label: "Oct", visual: 64, audio: 0, puzzle: 15, overall: 31 },
    { label: "Nov", visual: 60, audio: 0, puzzle: 13, overall: 29 },
    { label: "Dec", visual: 55, audio: 0, puzzle: 10, overall: 26 },
  ],
};

export default function DashboardView({ onNavigate }: DashboardViewProps) {
  const [activeTab, setActiveTab] = useState<"Market" | "Wallet" | "Tools">("Wallet");
  const [timeFilter, setTimeFilter] = useState<"1D" | "1W" | "1M" | "6M" | "1Y">("1Y");
  const [watchlistFilter, setWatchlistFilter] = useState<"Most Viewed" | "Gain" | "Lose">("Most Viewed");
  const [holdingFilter, setHoldingFilter] = useState<"6M" | "1Y" | "All">("6M");

  const chartData = PERFORMANCE_DATA_SETS[timeFilter] || PERFORMANCE_DATA_SETS["1Y"];

  const watchlistItems = [
    {
      name: "Visual (CLIP ViT-B/32)",
      ticker: "HF: openai/clip",
      accuracy: "84.7%",
      f1: "F1: 0.794",
      delta: "+13.1%",
      isPositive: true,
      icon: Eye,
      iconColor: "#a855f7",
    },
    {
      name: "Audio (Wav2Vec2)",
      ticker: "HF: meta/wav2vec2",
      accuracy: "0.0%",
      f1: "CER: 1.288",
      delta: "-100.0%",
      isPositive: false,
      icon: Mic,
      iconColor: "#ec4899",
    },
    {
      name: "Puzzle (OpenCV Canny)",
      ticker: "EDGE: slider-crack",
      accuracy: "25.0%",
      f1: "Err: 92.4px",
      delta: "-75.0%",
      isPositive: false,
      icon: Puzzle,
      iconColor: "#f59e0b",
    },
    {
      name: "Multimodal Router",
      ticker: "FASTAPI: rule-dispatch",
      accuracy: "100.0%",
      f1: "Latency: 1.4ms",
      delta: "+0.0%",
      isPositive: true,
      icon: Network,
      iconColor: "#10b981",
    },
  ];

  const filteredWatchlist = watchlistItems.filter((item) => {
    if (watchlistFilter === "Gain") return item.isPositive;
    if (watchlistFilter === "Lose") return !item.isPositive;
    return true;
  });

  return (
    <div className="p-8 space-y-6 max-w-[1550px] mx-auto min-h-screen text-white">
      {/* Top Header Row matching "Welcome, Nadia" aesthetic */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight flex items-center gap-2">
            Welcome, <span className="text-[#e879f9]">Researcher</span>
          </h1>
          <p className="text-sm mt-1 text-[#84899e] font-normal">
            Here&apos;s your CAPTCHA security &amp; robustness benchmark overview
          </p>

          {/* Sub Header Navigation Pills (Market, Wallet, Tools style) */}
          <div className="flex items-center gap-2 mt-5">
            {(["Market", "Wallet", "Tools"] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-5 py-2 text-xs font-medium rounded-full transition-all duration-200 ${
                  activeTab === tab
                    ? "helios-pill-active"
                    : "helios-pill text-gray-400 hover:text-white"
                }`}
              >
                {tab === "Market" ? "All Modalities" : tab === "Wallet" ? "Robustness Audit" : "Ablation Tools"}
              </button>
            ))}
          </div>
        </div>

        {/* Top Right Controls & Profile */}
        <div className="flex items-center gap-4 flex-wrap">
          {/* Ask helios.ai anything pill bar */}
          <div className="relative flex items-center">
            <Search className="w-4 h-4 text-gray-400 absolute left-4" />
            <input
              type="text"
              placeholder="Ask recaptcha.ai anything"
              className="pl-11 pr-10 py-2.5 rounded-full text-xs font-normal text-white placeholder-gray-500 focus:outline-none focus:border-pink-500/50 transition-all w-64 lg:w-72"
              style={{
                background: "#181922",
                border: "1px solid rgba(255, 255, 255, 0.08)",
              }}
            />
            <Sparkles className="w-3.5 h-3.5 text-pink-400 absolute right-4" />
          </div>

          {/* Action icon buttons */}
          <button
            className="w-10 h-10 rounded-full flex items-center justify-center transition-all hover:bg-white/10"
            style={{
              background: "#181922",
              border: "1px solid rgba(255, 255, 255, 0.08)",
            }}
          >
            <Bell className="w-4 h-4 text-gray-300" />
          </button>

          <button
            onClick={() => onNavigate?.("live")}
            className="w-10 h-10 rounded-full flex items-center justify-center transition-all hover:bg-white/10"
            style={{
              background: "#181922",
              border: "1px solid rgba(255, 255, 255, 0.08)",
            }}
          >
            <SettingsIcon className="w-4 h-4 text-gray-300" />
          </button>

          {/* User Profile Badge */}
          <div
            className="flex items-center gap-3 pl-2 pr-4 py-1.5 rounded-full"
            style={{
              background: "#181922",
              border: "1px solid rgba(255, 255, 255, 0.08)",
            }}
          >
            <div
              className="w-8 h-8 rounded-full flex items-center justify-center font-bold text-xs"
              style={{
                background: "linear-gradient(135deg, #ec4899, #a855f7)",
                color: "#ffffff",
              }}
            >
              AL
            </div>
            <div className="text-left">
              <p className="text-xs font-semibold text-white leading-tight">Academic Lead</p>
              <p className="text-[10px] text-gray-400">eval@recaptcha-x.edu</p>
            </div>
          </div>
        </div>
      </div>

      {/* Main 3-Column Top Section */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-5">
        {/* Column 1: Left Stack (Total Holding + Decisions Powered by Data) */}
        <div className="md:col-span-12 lg:col-span-3 flex flex-col gap-5">
          {/* Card 1: Total Holding style */}
          <div className="helios-card p-6 flex flex-col justify-between flex-1 min-h-[170px]">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-[#8c91a6]">Total Challenges</span>
              <button
                onClick={() => setHoldingFilter(holdingFilter === "6M" ? "1Y" : "6M")}
                className="flex items-center gap-1.5 px-3 py-1 text-[11px] rounded-full helios-pill"
              >
                <span>74 Total</span>
                <ChevronDown className="w-3 h-3 text-gray-400" />
              </button>
            </div>

            <div className="my-2">
              <h2 className="text-3xl font-bold tracking-tight text-white">
                74 <span className="text-lg font-medium text-gray-400">Samples</span>
              </h2>
              <div className="flex items-center gap-2 mt-2">
                <span className="text-xs text-green-400 font-semibold flex items-center gap-1">
                  <TrendingUp className="w-3 h-3" />
                  100%
                </span>
                <span className="text-xs text-gray-400">Router Classification</span>
              </div>
            </div>

            <p className="text-[11px] text-[#71768c]">
              21 Visual · 25 Audio · 28 Slider Puzzles
            </p>
          </div>

          {/* Card 2: Decisions Powered by Data style */}
          <div className="helios-card p-6 flex flex-col justify-between flex-1 min-h-[195px] relative">
            <div
              className="absolute -top-12 -left-12 w-48 h-48 rounded-full pointer-events-none opacity-20 blur-3xl"
              style={{ background: "#ec4899" }}
            />
            <div
              className="absolute -bottom-10 -right-10 w-44 h-44 rounded-full pointer-events-none opacity-25 blur-3xl"
              style={{ background: "#a855f7" }}
            />

            <div className="relative z-10">
              <h3 className="text-base font-semibold text-white tracking-tight">
                Decisions Powered by Data
              </h3>
              <p className="text-xs text-[#8c91a6] mt-2 leading-relaxed">
                Empirical evaluation across real-world datasets reveals critical zero-shot acoustic and spatial robustness gaps.
              </p>
            </div>

            <div className="relative z-10 pt-4">
              <button
                onClick={() => onNavigate?.("analysis")}
                className="w-full py-2.5 px-5 rounded-full text-xs font-semibold text-white helios-button-glow flex items-center justify-center gap-2 cursor-pointer"
              >
                <Sparkles className="w-3.5 h-3.5" />
                <span>Explore AI Insights</span>
              </button>
            </div>
          </div>
        </div>

        {/* Column 2: Center (Watchlist style) */}
        <div className="md:col-span-12 lg:col-span-4 helios-card p-6 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-5">
              <h3 className="text-base font-semibold text-white tracking-tight">Modality Leaderboard</h3>
              {/* Filter Pills */}
              <div className="flex items-center gap-1">
                {(["Most Viewed", "Gain", "Lose"] as const).map((filter) => (
                  <button
                    key={filter}
                    onClick={() => setWatchlistFilter(filter)}
                    className={`px-3 py-1 text-[11px] rounded-full transition-all ${
                      watchlistFilter === filter
                        ? "helios-pill-active"
                        : "helios-pill text-gray-400"
                    }`}
                  >
                    {filter === "Most Viewed" ? "All" : filter}
                  </button>
                ))}
              </div>
            </div>

            {/* List Rows */}
            <div className="space-y-4">
              {filteredWatchlist.map((item) => {
                const Icon = item.icon;
                return (
                  <div
                    key={item.name}
                    className="flex items-center justify-between p-2.5 rounded-2xl hover:bg-white/[0.03] transition-all cursor-pointer"
                    onClick={() => onNavigate?.("analysis")}
                  >
                    <div className="flex items-center gap-3">
                      <div
                        className="w-10 h-10 rounded-xl flex items-center justify-center"
                        style={{
                          background: `${item.iconColor}18`,
                          border: `1px solid ${item.iconColor}33`,
                        }}
                      >
                        <Icon className="w-5 h-5" style={{ color: item.iconColor }} />
                      </div>
                      <div>
                        <p className="text-xs font-semibold text-white">{item.name}</p>
                        <p className="text-[11px] text-[#71768c]">{item.ticker}</p>
                      </div>
                    </div>

                    <div className="text-right">
                      <p className="text-xs font-bold text-white">{item.accuracy}</p>
                      <span
                        className={`text-[11px] font-medium flex items-center justify-end gap-0.5 ${
                          item.isPositive ? "text-green-400" : "text-pink-400"
                        }`}
                      >
                        {item.isPositive ? (
                          <TrendingUp className="w-2.5 h-2.5" />
                        ) : (
                          <TrendingDown className="w-2.5 h-2.5" />
                        )}
                        {item.delta}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="pt-3 border-t border-white/[0.06] flex items-center justify-between text-[11px] text-[#71768c]">
            <span>Benchmark Split: 59 Real / 15 Synthetic</span>
            <button
              onClick={() => onNavigate?.("live")}
              className="text-pink-400 hover:text-pink-300 font-medium"
            >
              Test Live →
            </button>
          </div>
        </div>

        {/* Column 3: Right (My Portfolio 2x2 grid style) */}
        <div className="md:col-span-12 lg:col-span-5 helios-card p-6 flex flex-col justify-between">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-base font-semibold text-white tracking-tight">Modality Matrix</h3>
            <button
              onClick={() => onNavigate?.("analysis")}
              className="flex items-center gap-1.5 px-3 py-1 rounded-full helios-pill text-xs font-medium text-gray-300 hover:text-white"
            >
              <span>See all</span>
              <ArrowUpRight className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* 2x2 Matrix Cards */}
          <div className="grid grid-cols-2 gap-3.5">
            {/* Box 1: Visual CLIP */}
            <div className="p-4 rounded-2xl bg-[#13141b] border border-white/[0.05] hover:border-purple-500/30 transition-all">
              <div className="flex items-baseline justify-between">
                <span className="text-lg font-bold text-white">84.7%</span>
                <span className="text-[10px] text-green-400 font-semibold">+13.1% (Gap)</span>
              </div>
              <div className="flex items-center justify-between mt-3">
                <div className="flex items-center gap-2">
                  <div className="w-6 h-6 rounded-lg bg-purple-500/15 flex items-center justify-center">
                    <Eye className="w-3.5 h-3.5 text-purple-400" />
                  </div>
                  <span className="text-xs font-medium text-gray-300">Visual CLIP</span>
                </div>
                <span className="text-[10px] text-[#71768c]">16 Grids</span>
              </div>
            </div>

            {/* Box 2: Audio Wav2Vec2 */}
            <div className="p-4 rounded-2xl bg-[#13141b] border border-white/[0.05] hover:border-pink-500/30 transition-all">
              <div className="flex items-baseline justify-between">
                <span className="text-lg font-bold text-pink-400">0.0%</span>
                <span className="text-[10px] text-pink-400 font-semibold">-100% (Gap)</span>
              </div>
              <div className="flex items-center justify-between mt-3">
                <div className="flex items-center gap-2">
                  <div className="w-6 h-6 rounded-lg bg-pink-500/15 flex items-center justify-center">
                    <Mic className="w-3.5 h-3.5 text-pink-400" />
                  </div>
                  <span className="text-xs font-medium text-gray-300">Audio ASR</span>
                </div>
                <span className="text-[10px] text-[#71768c]">20 SecurImage</span>
              </div>
            </div>

            {/* Box 3: Slider Puzzle */}
            <div className="p-4 rounded-2xl bg-[#13141b] border border-white/[0.05] hover:border-amber-500/30 transition-all">
              <div className="flex items-baseline justify-between">
                <span className="text-lg font-bold text-amber-400">25.0%</span>
                <span className="text-[10px] text-amber-400 font-semibold">92.4px Err</span>
              </div>
              <div className="flex items-center justify-between mt-3">
                <div className="flex items-center gap-2">
                  <div className="w-6 h-6 rounded-lg bg-amber-500/15 flex items-center justify-center">
                    <Puzzle className="w-3.5 h-3.5 text-amber-400" />
                  </div>
                  <span className="text-xs font-medium text-gray-300">OpenCV Puzzle</span>
                </div>
                <span className="text-[10px] text-[#71768c]">20 Slides</span>
              </div>
            </div>

            {/* Box 4: Multimodal Router */}
            <div className="p-4 rounded-2xl bg-[#13141b] border border-white/[0.05] hover:border-green-500/30 transition-all">
              <div className="flex items-baseline justify-between">
                <span className="text-lg font-bold text-green-400">100.0%</span>
                <span className="text-[10px] text-green-400 font-semibold">&lt;1.5ms</span>
              </div>
              <div className="flex items-center justify-between mt-3">
                <div className="flex items-center gap-2">
                  <div className="w-6 h-6 rounded-lg bg-green-500/15 flex items-center justify-center">
                    <Network className="w-3.5 h-3.5 text-green-400" />
                  </div>
                  <span className="text-xs font-medium text-gray-300">Router</span>
                </div>
                <span className="text-[10px] text-[#71768c]">74 Tests</span>
              </div>
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-white/[0.06] flex items-center gap-2 text-[11px] text-amber-400/90">
            <ShieldAlert className="w-3.5 h-3.5 flex-shrink-0" />
            <span>Finding: Zero-shot foundation models fail sharply on acoustic distortion.</span>
          </div>
        </div>
      </div>

      {/* Bottom Full-Width Section: Portfolio Performance Chart (Exact Helios Style) */}
      <div className="helios-card p-6 md:p-8">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
          <div>
            <h3 className="text-lg font-semibold text-white tracking-tight">
              Benchmark Performance &amp; Robustness Curves
            </h3>
            <p className="text-xs text-[#84899e] mt-0.5">
              Empirical resilience across synthetic variations, adversarial noise levels, and real-world distributions
            </p>
          </div>

          {/* Timeframe Filter Pills (1D, 1W, 1M, 6M, 1Y) */}
          <div className="flex items-center gap-1.5 p-1 rounded-full bg-[#12131b] border border-white/[0.06]">
            {(["1D", "1W", "1M", "6M", "1Y"] as const).map((period) => (
              <button
                key={period}
                onClick={() => setTimeFilter(period)}
                className={`px-3.5 py-1 text-xs font-medium rounded-full transition-all ${
                  timeFilter === period
                    ? "helios-pill-active"
                    : "text-gray-400 hover:text-white"
                }`}
              >
                {period}
              </button>
            ))}
          </div>
        </div>

        {/* Large Glowing Wave Area Chart with Pinned Callout Card */}
        <div className="relative w-full h-[280px]">
          {/* Pinned Callout Tooltip matching the 1st Jun 2025: $16,500 (+35%) element */}
          <div
            className="absolute top-2 left-1/2 -translate-x-1/2 z-20 pointer-events-none flex flex-col items-center"
          >
            <div
              className="px-4 py-2 rounded-2xl shadow-2xl flex items-center gap-3 backdrop-blur-md"
              style={{
                background: "rgba(23, 24, 34, 0.95)",
                border: "1px solid rgba(255, 255, 255, 0.12)",
                boxShadow: "0 10px 30px rgba(0, 0, 0, 0.6)",
              }}
            >
              <div>
                <p className="text-[10px] text-gray-400 font-medium">Gaussian Blur σ=2.0</p>
                <p className="text-sm font-bold text-white mt-0.5">
                  68.4% Acc{" "}
                  <span className="text-[11px] text-green-400 font-semibold ml-1.5 px-1.5 py-0.5 rounded-full bg-green-500/10">
                    +16.3%
                  </span>
                </p>
              </div>
            </div>
            {/* Dashed vertical pointer line */}
            <div className="w-[1px] h-14 border-l border-dashed border-pink-400/60 my-1" />
            {/* Glowing Anchor Dot */}
            <div className="w-3.5 h-3.5 rounded-full bg-pink-400 ring-4 ring-pink-500/30 pulse-glow" />
          </div>

          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData} margin={{ top: 35, right: 10, left: -20, bottom: 0 }}>
              <defs>
                {/* Purple-to-pink gradient area fill */}
                <linearGradient id="heliosPinkArea" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#ec4899" stopOpacity={0.28} />
                  <stop offset="60%" stopColor="#a855f7" stopOpacity={0.08} />
                  <stop offset="100%" stopColor="#a855f7" stopOpacity={0.0} />
                </linearGradient>
                <filter id="neonGlow" x="-20%" y="-20%" width="140%" height="140%">
                  <feGaussianBlur stdDeviation="3" result="blur" />
                  <feComposite in="SourceGraphic" in2="blur" operator="over" />
                </filter>
              </defs>

              <XAxis
                dataKey="label"
                stroke="#6b7280"
                fontSize={11}
                tickLine={false}
                axisLine={false}
                dy={10}
              />
              <YAxis
                stroke="#6b7280"
                fontSize={10}
                tickLine={false}
                axisLine={false}
                domain={[0, 100]}
                ticks={[10, 30, 50, 70, 90]}
                tickFormatter={(val) => `${val}%`}
              />
              <Tooltip
                content={({ active, payload, label }) => {
                  if (!active || !payload?.length) return null;
                  const d = payload[0].payload;
                  return (
                    <div
                      className="p-3 rounded-2xl text-xs space-y-1"
                      style={{
                        background: "#181922",
                        border: "1px solid rgba(255, 255, 255, 0.1)",
                        boxShadow: "0 8px 30px rgba(0,0,0,0.5)",
                      }}
                    >
                      <p className="font-semibold text-white">{label} {d.raw ? `· ${d.raw}` : ""}</p>
                      <p className="text-purple-300">Visual (CLIP): {d.visual}%</p>
                      <p className="text-amber-300">Puzzle (OpenCV): {d.puzzle}%</p>
                      <p className="text-pink-400">Audio (Wav2Vec2): {d.audio}%</p>
                      <p className="text-green-400 font-bold">Overall Average: {d.overall}%</p>
                    </div>
                  );
                }}
              />

              <Area
                type="natural"
                dataKey="visual"
                stroke="#f472b6"
                strokeWidth={3}
                fill="url(#heliosPinkArea)"
                filter="url(#neonGlow)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Legend / Metrics Footer */}
        <div className="flex flex-wrap items-center justify-between gap-4 mt-6 pt-4 border-t border-white/[0.06] text-xs text-[#84899e]">
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-pink-400 shadow-[0_0_8px_#ec4899]" />
              <span className="text-gray-300">Visual CLIP Robustness</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-amber-400" />
              <span className="text-gray-400">OpenCV Puzzle Edge Match</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-pink-600" />
              <span className="text-gray-400">Audio LibriSpeech Gap</span>
            </div>
          </div>

          <div className="flex items-center gap-2 text-[11px] text-gray-500">
            <span>Evaluated against 74 test vectors</span>
            <span>•</span>
            <span>FastAPI Benchmark v1.0.0</span>
          </div>
        </div>
      </div>
    </div>
  );
}
