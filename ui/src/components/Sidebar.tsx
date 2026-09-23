"use client";

import type { ActiveView } from "@/app/page";
import {
  LayoutDashboard,
  BarChart3,
  FlaskConical,
  Layers,
  FileText,
  Settings,
  HelpCircle,
  ShieldCheck,
} from "lucide-react";

const NAV = [
  { id: "dashboard" as ActiveView, label: "Dashboard", icon: LayoutDashboard },
  { id: "analysis" as ActiveView, label: "Analysis", icon: BarChart3 },
  { id: "live" as ActiveView, label: "Live Test", icon: FlaskConical },
];

export default function Sidebar({
  activeView,
  setActiveView,
}: {
  activeView: ActiveView;
  setActiveView: (v: ActiveView) => void;
}) {
  return (
    <aside
      className="w-64 flex-shrink-0 flex flex-col py-6 px-4 gap-2 h-full justify-between"
      style={{
        background: "#121318",
        borderRight: "1px solid rgba(255, 255, 255, 0.06)",
      }}
    >
      <div>
        {/* Logo / Header (Helios style) */}
        <div className="flex items-center gap-3 mb-8 px-2">
          <div
            className="w-10 h-10 rounded-xl flex items-center justify-center relative shadow-lg"
            style={{
              background: "linear-gradient(135deg, #a855f7, #ec4899)",
              boxShadow: "0 0 25px rgba(236,72,153,0.35)",
            }}
          >
            {/* Custom stylized dual-arch logo similar to the Helios icon */}
            <div className="flex items-center gap-1">
              <div className="w-1.5 h-5 bg-white rounded-full" />
              <div className="w-1.5 h-3 bg-white/70 rounded-full" />
              <div className="w-1.5 h-5 bg-white rounded-full" />
            </div>
          </div>
          <div>
            <p className="font-bold text-base text-white tracking-tight flex items-center gap-1.5">
              reCAPTCHA-X
            </p>
            <p className="text-[11px] font-medium" style={{ color: "#7a7f94" }}>
              Robustness Lab
            </p>
          </div>
        </div>

        {/* Main Nav Items */}
        <div className="space-y-1.5">
          {NAV.map(({ id, label, icon: Icon }) => {
            const isActive = activeView === id;
            return (
              <button
                key={id}
                onClick={() => setActiveView(id)}
                className={`flex items-center gap-3.5 w-full px-4 py-3 rounded-2xl text-sm font-medium transition-all duration-200 ${
                  isActive
                    ? "text-white shadow-lg"
                    : "text-gray-400 hover:text-gray-200 hover:bg-white/[0.04]"
                }`}
                style={
                  isActive
                    ? {
                        background:
                          "linear-gradient(135deg, rgba(236, 72, 153, 0.2), rgba(168, 85, 247, 0.15))",
                        border: "1px solid rgba(236, 72, 153, 0.35)",
                        boxShadow: "0 4px 20px rgba(236, 72, 153, 0.15)",
                      }
                    : { border: "1px solid transparent" }
                }
              >
                <Icon
                  className={`w-4 h-4 transition-colors ${
                    isActive ? "text-pink-400" : "text-gray-400"
                  }`}
                />
                <span className="tracking-wide">{label}</span>
              </button>
            );
          })}

          <button
            onClick={() => setActiveView("analysis")}
            className="flex items-center gap-3.5 w-full px-4 py-3 rounded-2xl text-sm font-medium text-gray-400 hover:text-gray-200 hover:bg-white/[0.04] transition-all"
          >
            <Layers className="w-4 h-4 text-gray-400" />
            <span className="tracking-wide">Model Matrix</span>
          </button>

          <a
            href="https://github.com/arjun143327/recaptcha-x-lab"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-3.5 w-full px-4 py-3 rounded-2xl text-sm font-medium text-gray-400 hover:text-gray-200 hover:bg-white/[0.04] transition-all"
          >
            <FileText className="w-4 h-4 text-gray-400" />
            <span className="tracking-wide">Research Paper</span>
          </a>
        </div>
      </div>

      {/* Bottom Nav / Settings */}
      <div className="space-y-1 pt-4 border-t border-white/[0.06]">
        <button
          onClick={() => setActiveView("dashboard")}
          className="flex items-center gap-3.5 w-full px-4 py-2.5 rounded-xl text-xs font-medium text-gray-400 hover:text-gray-200 hover:bg-white/[0.04] transition-all"
        >
          <Settings className="w-4 h-4 text-gray-400" />
          <span>Evaluation Settings</span>
        </button>
        <a
          href="https://github.com/arjun143327/recaptcha-x-lab"
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-3.5 w-full px-4 py-2.5 rounded-xl text-xs font-medium text-gray-400 hover:text-gray-200 hover:bg-white/[0.04] transition-all"
        >
          <HelpCircle className="w-4 h-4 text-gray-400" />
          <span>Documentation & Support</span>
        </a>

        {/* Academic Tag */}
        <div className="px-4 pt-3 flex items-center gap-2 text-[11px] text-gray-500">
          <ShieldCheck className="w-3.5 h-3.5 text-pink-400/80" />
          <span>Academic Security Lab</span>
        </div>
      </div>
    </aside>
  );
}
