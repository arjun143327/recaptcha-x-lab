"use client";

import { useState } from "react";
import Sidebar from "@/components/Sidebar";
import DashboardView from "@/components/DashboardView";
import AnalysisView from "@/components/AnalysisView";
import LiveTestView from "@/components/LiveTestView";

export type ActiveView = "dashboard" | "analysis" | "live";

export default function Home() {
  const [activeView, setActiveView] = useState<ActiveView>("dashboard");

  return (
    <div
      className="min-h-screen w-full flex items-center justify-center p-2 sm:p-4 lg:p-6 overflow-hidden relative"
      style={{
        background: "#0c0d12",
        backgroundImage:
          "radial-gradient(ellipse at 85% 15%, rgba(236, 72, 153, 0.08) 0%, transparent 50%), radial-gradient(ellipse at 15% 85%, rgba(168, 85, 247, 0.07) 0%, transparent 55%)",
      }}
    >
      {/* Outer Shell mimicking the reference screenshot window frame */}
      <div
        className="w-full max-w-[1680px] h-[96vh] rounded-[28px] lg:rounded-[36px] overflow-hidden flex flex-col md:flex-row relative shadow-2xl"
        style={{
          background: "#13141b",
          border: "1px solid rgba(255, 255, 255, 0.08)",
          boxShadow: "0 25px 80px -15px rgba(0, 0, 0, 0.9), 0 0 40px rgba(168, 85, 247, 0.05)",
        }}
      >
        <Sidebar activeView={activeView} setActiveView={setActiveView} />
        <main className="flex-1 overflow-y-auto bg-[#13141b]/80 backdrop-blur-md">
          {activeView === "dashboard" && <DashboardView onNavigate={setActiveView} />}
          {activeView === "analysis" && <AnalysisView />}
          {activeView === "live" && <LiveTestView />}
        </main>
      </div>
    </div>
  );
}
