export const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface SolveResult {
  predicted_type: "audio" | "visual" | "puzzle";
  router_confidence: number;
  specialist_used: string;
  answer: string | number | number[];
  specialist_confidence: number;
  details: Record<string, unknown>;
  elapsed_ms: number;
  filename: string;
}

export async function solveFile(file: File, prompt?: string): Promise<SolveResult> {
  const form = new FormData();
  form.append("file", file);
  if (prompt) form.append("prompt", prompt);

  const res = await fetch(`${API_BASE}/api/solve`, {
    method: "POST",
    body: form,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? "Unknown API error");
  }
  return res.json();
}

export async function fetchHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/api/health`, { cache: "no-store" });
    return res.ok;
  } catch {
    return false;
  }
}
