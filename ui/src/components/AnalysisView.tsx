"use client";

import { useState } from "react";
import { PRECOMPUTED_METRICS } from "@/lib/metrics";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  Cell,
  LineChart,
  Line,
  ScatterChart,
  Scatter,
  ZAxis,
} from "recharts";

const m = PRECOMPUTED_METRICS;

type Tab = "visual" | "audio" | "puzzle";

const TABS: { id: Tab; label: string; emoji: string }[] = [
  { id: "visual", label: "Visual (CLIP)", emoji: "👁️" },
  { id: "audio", label: "Audio (Wav2Vec2)", emoji: "🎙️" },
  { id: "puzzle", label: "Puzzle (OpenCV)", emoji: "🧩" },
];

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div
      className="rounded-xl p-3 text-xs"
      style={{
        background: "#1a1a20",
        border: "1px solid rgba(255,255,255,0.1)",
      }}
    >
      <p className="font-semibold text-white mb-1">{label}</p>
      {payload.map((p: any) => (
        <p key={p.dataKey} style={{ color: p.fill ?? p.stroke }}>
          {p.name}: {typeof p.value === "number" ? p.value.toFixed(2) : p.value}
        </p>
      ))}
    </div>
  );
};

function VisualAnalysis() {
  const perClass = [...m.visual.per_class].sort((a, b) => a.f1 - b.f1);
  return (
    <div className="space-y-6">
      {/* Summary row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: "Real Cell Accuracy", value: (m.visual.real_cell_accuracy * 100).toFixed(1) + "%" },
          { label: "Real F1 Score", value: m.visual.real_f1.toFixed(4) },
          { label: "Exact Grid Match", value: (m.visual.exact_match_rate * 100).toFixed(1) + "%" },
          { label: "Samples", value: m.visual.num_samples },
        ].map(({ label, value }) => (
          <div key={label} className="glass-card p-4 text-center">
            <p className="text-2xl font-bold text-purple-400">{value}</p>
            <p className="text-xs mt-1" style={{ color: "var(--text-muted)" }}>{label}</p>
          </div>
        ))}
      </div>

      {/* Per-class F1 */}
      <div className="glass-card p-6">
        <h3 className="font-semibold text-white mb-4">F1 Score by Object Category</h3>
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={perClass} layout="vertical" barCategoryGap="20%">
            <CartesianGrid horizontal={false} stroke="rgba(255,255,255,0.05)" />
            <XAxis type="number" domain={[0, 1]} tick={{ fill: "#6b7280", fontSize: 11 }} axisLine={false} tickLine={false} />
            <YAxis type="category" dataKey="label" width={100} tick={{ fill: "#9ca3af", fontSize: 11 }} axisLine={false} tickLine={false} />
            <Tooltip content={<CustomTooltip />} />
            <Bar dataKey="f1" name="F1 Score" radius={[0, 4, 4, 0]}>
              {perClass.map((entry) => (
                <Cell
                  key={entry.label}
                  fill={entry.f1 >= 0.85 ? "#10b981" : entry.f1 >= 0.75 ? "#a855f7" : "#ef4444"}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
        <div className="flex gap-4 mt-3">
          {[["#10b981", "≥0.85 Good"], ["#a855f7", "≥0.75 Fair"], ["#ef4444", "<0.75 Poor"]].map(([c, l]) => (
            <div key={l} className="flex items-center gap-1.5 text-xs" style={{ color: "var(--text-muted)" }}>
              <div className="w-2.5 h-2.5 rounded-sm" style={{ background: c }} />
              {l}
            </div>
          ))}
        </div>
      </div>

      {/* Real vs synth comparison */}
      <div className="glass-card p-6">
        <h3 className="font-semibold text-white mb-4">Real vs Synthetic Performance Gap</h3>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart
            data={[
              { label: "Cell Accuracy", real: m.visual.real_cell_accuracy * 100, synth: m.visual.synth_cell_accuracy * 100 },
              { label: "F1 Score", real: m.visual.real_f1 * 100, synth: m.visual.synth_f1 * 100 },
            ]}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
            <XAxis dataKey="label" tick={{ fill: "#9ca3af", fontSize: 12 }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fill: "#6b7280", fontSize: 11 }} axisLine={false} tickLine={false} unit="%" domain={[0, 100]} />
            <Tooltip content={<CustomTooltip />} />
            <Bar dataKey="synth" name="Synthetic" fill="#a855f7" radius={[4, 4, 0, 0]} />
            <Bar dataKey="real" name="Real" fill="#ec4899" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

function AudioAnalysis() {
  const cerData = m.audio.real_samples.map((s) => ({
    name: s.id.substring(0, 6),
    cer: +(s.cer * 100).toFixed(0),
    lev: s.lev_dist,
  }));

  return (
    <div className="space-y-6">
      {/* Summary */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: "Synth Exact Match", value: "100%", good: true },
          { label: "Real Exact Match", value: "0%", good: false },
          { label: "Real CER", value: (m.audio.real_cer * 100).toFixed(0) + "%", good: false },
          { label: "Synth CER", value: "0%", good: true },
        ].map(({ label, value, good }) => (
          <div key={label} className="glass-card p-4 text-center">
            <p className={`text-2xl font-bold ${good ? "text-green-400" : "text-pink-400"}`}>{value}</p>
            <p className="text-xs mt-1" style={{ color: "var(--text-muted)" }}>{label}</p>
          </div>
        ))}
      </div>

      {/* Domain gap highlight */}
      <div
        className="glass-card p-5 rounded-xl"
        style={{ borderColor: "rgba(236,72,153,0.3)", background: "rgba(236,72,153,0.05)" }}
      >
        <div className="flex items-start gap-3">
          <span className="text-2xl">⚠️</span>
          <div>
            <p className="font-semibold text-white">Acoustic Domain Gap Detected</p>
            <p className="text-xs mt-1 leading-relaxed" style={{ color: "#d1d5db" }}>
              <strong>facebook/wav2vec2-base-960h</strong> was pretrained on LibriSpeech — clean audiobook recordings.
              Real SecurImage challenges apply synthetic multi-speaker overlap, white noise masking, pitch jitter, and
              reverberation specifically designed to defeat speech-recognition models. This explains the 0% real-world
              accuracy despite 100% performance on clean TTS-generated CAPTCHA audio.
            </p>
          </div>
        </div>
      </div>

      {/* CER per-sample bar chart */}
      <div className="glass-card p-6">
        <h3 className="font-semibold text-white mb-4">Character Error Rate per Real Sample</h3>
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={cerData}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
            <XAxis dataKey="name" tick={{ fill: "#9ca3af", fontSize: 11 }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fill: "#6b7280", fontSize: 11 }} axisLine={false} tickLine={false} unit="%" domain={[0, 200]} />
            <Tooltip content={<CustomTooltip />} />
            <Bar dataKey="cer" name="CER (%)" fill="#ec4899" radius={[4, 4, 0, 0]} opacity={0.85} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Levenshtein distances */}
      <div className="glass-card p-6">
        <h3 className="font-semibold text-white mb-4">Levenshtein Distance per Real Sample</h3>
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={cerData}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
            <XAxis dataKey="name" tick={{ fill: "#9ca3af", fontSize: 11 }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fill: "#6b7280", fontSize: 11 }} axisLine={false} tickLine={false} />
            <Tooltip content={<CustomTooltip />} />
            <Line dataKey="lev" name="Lev. Distance" stroke="#a855f7" strokeWidth={2} dot={{ fill: "#a855f7", r: 4 }} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

function PuzzleAnalysis() {
  const errorBins = m.puzzle.error_bins;
  const accuracyBreakdown = [
    { name: "Synthetic", accuracy: m.puzzle.synth_accuracy * 100, error: m.puzzle.synth_mean_error },
    { name: "Demo Showcase", accuracy: m.puzzle.demo_accuracy * 100, error: m.puzzle.demo_mean_error },
    { name: "Independent Real", accuracy: m.puzzle.independent_real_accuracy * 100, error: m.puzzle.independent_real_mean_error },
  ];

  return (
    <div className="space-y-6">
      {/* Summary */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: "Synth Accuracy", value: "100%", good: true },
          { label: "Demo Accuracy", value: (m.puzzle.demo_accuracy * 100).toFixed(0) + "%", good: false },
          { label: "Indep. Real Accuracy", value: "25%", good: false },
          { label: "Mean Pixel Error (Real)", value: m.puzzle.independent_real_mean_error + "px", good: false },
        ].map(({ label, value, good }) => (
          <div key={label} className="glass-card p-4 text-center">
            <p className={`text-2xl font-bold ${good ? "text-green-400" : "text-amber-400"}`}>{value}</p>
            <p className="text-xs mt-1" style={{ color: "var(--text-muted)" }}>{label}</p>
          </div>
        ))}
      </div>

      {/* Leakage warning */}
      <div
        className="glass-card p-5"
        style={{ borderColor: "rgba(245,158,11,0.3)", background: "rgba(245,158,11,0.05)" }}
      >
        <div className="flex items-start gap-3">
          <span className="text-2xl">🔬</span>
          <div>
            <p className="font-semibold text-white">Demo Leakage Identified & Separated</p>
            <p className="text-xs mt-1 leading-relaxed" style={{ color: "#d1d5db" }}>
              Initial 3 puzzle samples sourced from source repository README showcase examples (peduajo/geetest-slice-captcha-solver
              and Henryhaohao/Slider_Captcha_Crack) were confirmed to be demo images used during algorithm development.
              These are now tracked separately. The 20 independent real samples come from the official validation split
              of Python3WebSpider/DeepLearningSlideCaptcha and the MossLinn HarmonyOS GUI benchmark.
            </p>
          </div>
        </div>
      </div>

      {/* Accuracy breakdown */}
      <div className="glass-card p-6">
        <h3 className="font-semibold text-white mb-4">Accuracy & Mean Error by Data Source</h3>
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={accuracyBreakdown}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
            <XAxis dataKey="name" tick={{ fill: "#9ca3af", fontSize: 12 }} axisLine={false} tickLine={false} />
            <YAxis yAxisId="left" tick={{ fill: "#6b7280", fontSize: 11 }} axisLine={false} tickLine={false} unit="%" domain={[0, 100]} />
            <YAxis yAxisId="right" orientation="right" tick={{ fill: "#6b7280", fontSize: 11 }} axisLine={false} tickLine={false} unit="px" />
            <Tooltip content={<CustomTooltip />} />
            <Bar yAxisId="left" dataKey="accuracy" name="Accuracy (%)" fill="#a855f7" radius={[4, 4, 0, 0]} />
            <Bar yAxisId="right" dataKey="error" name="Mean Error (px)" fill="#f59e0b" radius={[4, 4, 0, 0]} opacity={0.75} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Error distribution */}
      <div className="glass-card p-6">
        <h3 className="font-semibold text-white mb-4">Pixel Error Distribution (All Real Samples)</h3>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={errorBins}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
            <XAxis dataKey="range" tick={{ fill: "#9ca3af", fontSize: 11 }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fill: "#6b7280", fontSize: 11 }} axisLine={false} tickLine={false} />
            <Tooltip content={<CustomTooltip />} />
            <Bar dataKey="count" name="Sample Count" radius={[4, 4, 0, 0]}>
              {errorBins.map((entry, i) => (
                <Cell key={i} fill={i < 2 ? "#10b981" : i < 3 ? "#a855f7" : "#ef4444"} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export default function AnalysisView() {
  const [tab, setTab] = useState<Tab>("visual");

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white">
          Deep <span className="gradient-text">Analysis</span>
        </h1>
        <p className="text-sm mt-1" style={{ color: "var(--text-muted)" }}>
          Per-modality breakdown — metrics, domain gaps, and data leakage audit
        </p>
      </div>

      {/* Tab switcher */}
      <div
        className="flex gap-1 p-1 rounded-xl w-fit"
        style={{ background: "var(--bg-card)", border: "1px solid var(--border)" }}
      >
        {TABS.map(({ id, label, emoji }) => (
          <button
            key={id}
            onClick={() => setTab(id)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
              tab === id
                ? "text-white"
                : "text-gray-400 hover:text-gray-200"
            }`}
            style={
              tab === id
                ? {
                    background: "linear-gradient(135deg, rgba(168,85,247,0.3), rgba(236,72,153,0.2))",
                    border: "1px solid rgba(168,85,247,0.4)",
                  }
                : {}
            }
          >
            <span>{emoji}</span>
            {label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {tab === "visual" && <VisualAnalysis />}
      {tab === "audio" && <AudioAnalysis />}
      {tab === "puzzle" && <PuzzleAnalysis />}
    </div>
  );
}
