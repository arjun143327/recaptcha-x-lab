"use client";

import { useState, useCallback, useEffect } from "react";
import { solveFile, fetchHealth, type SolveResult } from "@/lib/api";
import { Upload, CheckCircle, XCircle, Loader2, AudioLines, Eye, Puzzle, Zap } from "lucide-react";

type Status = "idle" | "uploading" | "success" | "error";

const MODALITY_CONFIG = {
  audio: { label: "Audio CAPTCHA", icon: AudioLines, color: "#ec4899", bg: "rgba(236,72,153,0.1)" },
  visual: { label: "Visual Grid", icon: Eye, color: "#a855f7", bg: "rgba(168,85,247,0.1)" },
  puzzle: { label: "Slider Puzzle", icon: Puzzle, color: "#f59e0b", bg: "rgba(245,158,11,0.1)" },
};

function AnswerDisplay({ result }: { result: SolveResult }) {
  const cfg = MODALITY_CONFIG[result.predicted_type] ?? MODALITY_CONFIG.visual;

  const formatAnswer = () => {
    if (result.predicted_type === "visual") {
      const cells = Array.isArray(result.answer) ? (result.answer as number[]) : [];
      return (
        <div className="space-y-2">
          <p className="text-xs" style={{ color: "var(--text-muted)" }}>Matched grid cells:</p>
          <div className="grid grid-cols-3 gap-1.5 w-28">
            {Array.from({ length: 9 }, (_, i) => (
              <div
                key={i}
                className="aspect-square rounded-md flex items-center justify-center text-xs font-bold transition-all"
                style={{
                  background: cells.includes(i)
                    ? "linear-gradient(135deg, #a855f7, #ec4899)"
                    : "rgba(255,255,255,0.06)",
                  color: cells.includes(i) ? "white" : "#4b5563",
                }}
              >
                {i}
              </div>
            ))}
          </div>
          <p className="text-xs text-purple-400">Cells: [{(result.answer as number[]).join(", ")}]</p>
        </div>
      );
    }
    if (result.predicted_type === "audio") {
      return (
        <div className="space-y-1">
          <p className="text-xs" style={{ color: "var(--text-muted)" }}>Transcribed text:</p>
          <p className="text-2xl font-mono font-bold text-pink-400 tracking-widest">
            {String(result.answer).toUpperCase() || "—"}
          </p>
        </div>
      );
    }
    if (result.predicted_type === "puzzle") {
      return (
        <div className="space-y-1">
          <p className="text-xs" style={{ color: "var(--text-muted)" }}>Slider offset (pixels):</p>
          <p className="text-3xl font-bold text-amber-400">{String(result.answer)}<span className="text-sm ml-1" style={{ color: "var(--text-muted)" }}>px</span></p>
        </div>
      );
    }
    return <p className="font-mono text-white">{JSON.stringify(result.answer)}</p>;
  };

  return (
    <div className="space-y-4">
      {/* Route result */}
      <div className="grid grid-cols-3 gap-3">
        <div className="glass-card p-3 text-center">
          <div className="flex items-center justify-center gap-1.5 mb-1">
            <cfg.icon className="w-4 h-4" style={{ color: cfg.color }} />
          </div>
          <p className="text-xs" style={{ color: "var(--text-muted)" }}>Detected Type</p>
          <p className="font-semibold text-sm text-white mt-0.5 capitalize">{result.predicted_type}</p>
        </div>
        <div className="glass-card p-3 text-center">
          <p className="text-xs" style={{ color: "var(--text-muted)" }}>Router Conf.</p>
          <p className="font-bold text-lg text-green-400 mt-0.5">{(result.router_confidence * 100).toFixed(1)}%</p>
        </div>
        <div className="glass-card p-3 text-center">
          <p className="text-xs" style={{ color: "var(--text-muted)" }}>Latency</p>
          <p className="font-bold text-lg text-blue-400 mt-0.5">{result.elapsed_ms}ms</p>
        </div>
      </div>

      {/* Answer */}
      <div className="glass-card p-4 space-y-3">
        <div className="flex items-center justify-between">
          <p className="text-sm font-semibold text-white">Specialist Answer</p>
          <span
            className="text-xs px-2 py-0.5 rounded-full font-medium"
            style={{ background: cfg.bg, color: cfg.color }}
          >
            {(result.specialist_confidence * 100).toFixed(1)}% conf.
          </span>
        </div>
        {formatAnswer()}
      </div>

      {/* Details */}
      <details className="glass-card p-4 group">
        <summary className="text-xs font-semibold text-gray-400 cursor-pointer select-none">
          Raw Details ▾
        </summary>
        <pre
          className="mt-3 text-xs overflow-auto rounded-lg p-3"
          style={{ background: "rgba(0,0,0,0.3)", color: "#9ca3af", maxHeight: "200px" }}
        >
          {JSON.stringify(result.details, null, 2)}
        </pre>
      </details>
    </div>
  );
}

export default function LiveTestView() {
  const [status, setStatus] = useState<Status>("idle");
  const [result, setResult] = useState<SolveResult | null>(null);
  const [error, setError] = useState<string>("");
  const [prompt, setPrompt] = useState("traffic light");
  const [dragging, setDragging] = useState(false);
  const [apiOnline, setApiOnline] = useState<boolean | null>(null);
  const [filename, setFilename] = useState<string>("");

  useEffect(() => {
    fetchHealth().then(setApiOnline);
    const interval = setInterval(() => fetchHealth().then(setApiOnline), 10000);
    return () => clearInterval(interval);
  }, []);

  const handleFile = useCallback(
    async (file: File) => {
      setStatus("uploading");
      setError("");
      setResult(null);
      setFilename(file.name);
      try {
        const res = await solveFile(file, prompt);
        setResult(res);
        setStatus("success");
      } catch (e: any) {
        setError(e.message ?? "Unknown error");
        setStatus("error");
      }
    },
    [prompt]
  );

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragging(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  const onInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  return (
    <div className="p-8 max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">
            Live <span className="gradient-text">Test</span>
          </h1>
          <p className="text-sm mt-1" style={{ color: "var(--text-muted)" }}>
            Upload any CAPTCHA challenge — the pipeline routes and solves it in real-time
          </p>
        </div>
        {/* API status */}
        <div
          className="flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium"
          style={{
            background: apiOnline ? "rgba(16,185,129,0.1)" : "rgba(239,68,68,0.1)",
            border: `1px solid ${apiOnline ? "rgba(16,185,129,0.3)" : "rgba(239,68,68,0.3)"}`,
            color: apiOnline ? "#10b981" : "#ef4444",
          }}
        >
          <span className={`w-1.5 h-1.5 rounded-full ${apiOnline ? "bg-green-400" : "bg-red-400"} pulse-dot`} />
          API {apiOnline === null ? "checking…" : apiOnline ? "Online" : "Offline — start api/main.py"}
        </div>
      </div>

      {/* How it works */}
      <div className="grid grid-cols-3 gap-3">
        {[
          { step: "1", label: "Upload File", desc: "WAV / PNG / JPG", icon: Upload, color: "#3b82f6" },
          { step: "2", label: "Router Classifies", desc: "Audio · Visual · Puzzle", icon: Zap, color: "#a855f7" },
          { step: "3", label: "Specialist Solves", desc: "Wav2Vec2 / CLIP / OpenCV", icon: CheckCircle, color: "#10b981" },
        ].map(({ step, label, desc, icon: Icon, color }) => (
          <div key={step} className="glass-card p-4 flex items-center gap-3">
            <div
              className="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0 text-xs font-bold"
              style={{ background: `${color}20`, color, border: `1px solid ${color}40` }}
            >
              {step}
            </div>
            <div>
              <p className="font-semibold text-sm text-white">{label}</p>
              <p className="text-xs" style={{ color: "var(--text-muted)" }}>{desc}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Prompt input (for visual) */}
      <div className="glass-card p-4 flex items-center gap-3">
        <Eye className="w-4 h-4 text-purple-400 flex-shrink-0" />
        <div className="flex-1">
          <label className="text-xs font-medium" style={{ color: "var(--text-muted)" }}>
            Visual Prompt (used only if file is a reCAPTCHA grid)
          </label>
          <input
            type="text"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            className="w-full mt-1 bg-transparent text-sm text-white outline-none placeholder:text-gray-600"
            placeholder="traffic light"
          />
        </div>
      </div>

      {/* Drop zone */}
      <label
        htmlFor="file-upload"
        className={`drop-zone glass-card rounded-2xl p-10 flex flex-col items-center gap-3 cursor-pointer ${dragging ? "dragging" : ""}`}
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
      >
        {status === "uploading" ? (
          <Loader2 className="w-10 h-10 text-purple-400 spinner" />
        ) : (
          <Upload className="w-10 h-10 text-purple-500" />
        )}
        <div className="text-center">
          <p className="font-semibold text-white text-sm">
            {status === "uploading" ? `Analysing ${filename}…` : "Drop your CAPTCHA file here"}
          </p>
          <p className="text-xs mt-1" style={{ color: "var(--text-muted)" }}>
            Supported: .wav · .mp3 · .png · .jpg
          </p>
        </div>
        <input
          id="file-upload"
          type="file"
          accept=".wav,.mp3,.png,.jpg,.jpeg"
          className="hidden"
          onChange={onInputChange}
          disabled={status === "uploading"}
        />
      </label>

      {/* Error */}
      {status === "error" && (
        <div
          className="glass-card p-4 flex items-center gap-3"
          style={{ borderColor: "rgba(239,68,68,0.4)", background: "rgba(239,68,68,0.05)" }}
        >
          <XCircle className="w-5 h-5 text-red-400 flex-shrink-0" />
          <div>
            <p className="font-semibold text-sm text-red-400">Error</p>
            <p className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>{error}</p>
          </div>
        </div>
      )}

      {/* Result */}
      {status === "success" && result && <AnswerDisplay result={result} />}

      {/* Sample file hints */}
      {status === "idle" && (
        <div className="glass-card p-4">
          <p className="text-xs font-semibold text-gray-400 mb-3">Try with your benchmark samples:</p>
          <div className="grid grid-cols-3 gap-2 text-xs" style={{ color: "var(--text-muted)" }}>
            {[
              { label: "🎙️ Audio", path: "data/audio/real_audio_017ddc45.wav" },
              { label: "👁️ Visual", path: "data/visual/real_recaptcha_chimney.jpg" },
              { label: "🧩 Puzzle", path: "data/puzzle/real_puzzle_slide_0010.png" },
            ].map(({ label, path }) => (
              <div key={path} className="rounded-lg p-2.5" style={{ background: "rgba(255,255,255,0.03)", border: "1px solid var(--border)" }}>
                <p className="font-medium text-gray-300 mb-1">{label}</p>
                <p className="font-mono break-all" style={{ fontSize: "10px" }}>{path}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
