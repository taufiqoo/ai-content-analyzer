"use client";
import { useState, useEffect } from "react";
import Sidebar from "@/components/Sidebar";
import { ToastProvider } from "@/components/Toast";
import { jobsApi, scriptsApi } from "@/lib/api";

function AnalyticsContent() {
  const [summary, setSummary] = useState<any>(null);
  const [scripts, setScripts] = useState<any[]>([]);

  useEffect(() => {
    jobsApi.getSummary().then(setSummary).catch(() => {});
    scriptsApi.list({ status: "approved" }).then(setScripts).catch(() => {});
  }, []);

  // Aggregate hook formula performance
  const hookStats: Record<string, { count: number; fyp: number; views: number }> = {};
  const angleStats: Record<string, { count: number; fyp: number; views: number }> = {};

  scripts.forEach((s) => {
    const perf = s.performance;
    const hook = s.hook_formula_used || "Unknown";
    const angle = s.angle || "Unknown";

    if (!hookStats[hook]) hookStats[hook] = { count: 0, fyp: 0, views: 0 };
    hookStats[hook].count++;
    if (perf?.did_fyp) hookStats[hook].fyp++;
    hookStats[hook].views += perf?.views || 0;

    if (!angleStats[angle]) angleStats[angle] = { count: 0, fyp: 0, views: 0 };
    angleStats[angle].count++;
    if (perf?.did_fyp) angleStats[angle].fyp++;
    angleStats[angle].views += perf?.views || 0;
  });

  const topHooks = Object.entries(hookStats)
    .sort(([, a], [, b]) => b.fyp - a.fyp || b.views - a.views)
    .slice(0, 5);

  const topAngles = Object.entries(angleStats)
    .sort(([, a], [, b]) => b.fyp - a.fyp || b.views - a.views);

  return (
    <div className="app-shell">
      <Sidebar />
      <main className="main-content">
        <div className="page-header">
          <h2 className="page-title">📊 Analytics</h2>
          <p className="page-subtitle">Track hook formula performance and content insights</p>
        </div>

        {/* Summary Stats */}
        <div className="stats-grid" style={{ marginBottom: "32px" }}>
          {[
            { label: "Total Scripts", value: summary?.scripts_total ?? "—", icon: "📝" },
            { label: "Approved", value: summary?.scripts_approved ?? "—", icon: "✅" },
            { label: "FYP Count 🚀", value: summary?.fyp_count ?? "—", icon: "🔥" },
            { label: "Total Views", value: summary?.total_views ? `${(summary.total_views / 1000).toFixed(1)}K` : "—", icon: "👁️" },
          ].map((s) => (
            <div key={s.label} className="stat-card">
              <div style={{ fontSize: "1.5rem", marginBottom: "8px" }}>{s.icon}</div>
              <div className="stat-value">{s.value}</div>
              <div className="stat-label">{s.label}</div>
            </div>
          ))}
        </div>

        <div className="grid-2">
          {/* Hook Formula Performance */}
          <div className="card">
            <div className="card-header">
              <div className="card-title">🎣 Top Hook Formulas</div>
              <div className="card-subtitle">By FYP count</div>
            </div>
            {topHooks.length === 0 ? (
              <div className="empty-state" style={{ padding: "32px 0" }}>
                <div className="empty-state-icon">📊</div>
                <div className="empty-state-title">No data yet</div>
                <div className="empty-state-desc">Approve scripts and log performance after posting to see analytics.</div>
              </div>
            ) : (
              topHooks.map(([formula, stats], i) => (
                <div key={formula} style={{ padding: "12px 0", borderBottom: "1px solid var(--border-subtle)" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "6px" }}>
                    <span style={{ fontSize: "0.8rem", color: "var(--text-primary)", flex: 1, marginRight: "8px" }}>
                      #{i + 1} {formula.slice(0, 60)}{formula.length > 60 ? "..." : ""}
                    </span>
                    <div style={{ display: "flex", gap: "12px", flexShrink: 0 }}>
                      <span style={{ fontSize: "0.75rem", color: "var(--success)" }}>{stats.fyp} FYP</span>
                      <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>{(stats.views / 1000).toFixed(0)}K views</span>
                    </div>
                  </div>
                  <div className="naturalness-track">
                    <div className="naturalness-fill" style={{ width: `${Math.min(100, (stats.views / 900000) * 100)}%` }} />
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Angle Performance */}
          <div className="card">
            <div className="card-header">
              <div className="card-title">🎬 Angle Performance</div>
              <div className="card-subtitle">Which angle works best?</div>
            </div>
            {topAngles.length === 0 ? (
              <div className="empty-state" style={{ padding: "32px 0" }}>
                <div className="empty-state-icon">🎭</div>
                <div className="empty-state-title">No data yet</div>
              </div>
            ) : (
              topAngles.map(([angle, stats]) => {
                const ANGLE_LABELS: Record<string, string> = {
                  hero: "🌟 Hero", tips_trick: "💡 Tips & Trick",
                  controversial: "🔥 Controversial", storytelling: "📖 Storytelling", reply_komen: "💬 Reply",
                };
                return (
                  <div key={angle} style={{ padding: "12px 0", borderBottom: "1px solid var(--border-subtle)" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "6px" }}>
                      <span style={{ fontSize: "0.875rem", color: "var(--text-primary)" }}>{ANGLE_LABELS[angle] || angle}</span>
                      <div style={{ display: "flex", gap: "12px" }}>
                        <span style={{ fontSize: "0.75rem", color: "var(--success)" }}>{stats.fyp} FYP</span>
                        <span style={{ fontSize: "0.75rem", color: "var(--info)" }}>{stats.count} scripts</span>
                      </div>
                    </div>
                    <div className="naturalness-track">
                      <div className="naturalness-fill" style={{ width: stats.count > 0 ? `${Math.min(100, (stats.fyp / stats.count) * 100)}%` : "0%" }} />
                    </div>
                    <div style={{ fontSize: "0.72rem", color: "var(--text-muted)", marginTop: "4px" }}>
                      FYP rate: {stats.count > 0 ? Math.round((stats.fyp / stats.count) * 100) : 0}%
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Proven Formula Reference */}
        <div className="card mt-6">
          <div className="card-header">
            <div className="card-title">🏆 Proven Formula Reference</div>
            <span className="badge badge-approved">Terbukti FYP 900K Views</span>
          </div>
          <div style={{ background: "var(--accent-dim)", border: "1px solid var(--border)", borderRadius: "var(--radius-md)", padding: "16px 20px" }}>
            <div style={{ fontSize: "0.9rem", fontWeight: 600, color: "var(--text-primary)", marginBottom: "8px" }}>
              🎣 Hook yang terbukti FYP:
            </div>
            <div style={{ fontSize: "0.95rem", color: "var(--text-primary)", lineHeight: 1.6 }}>
              "Para pemimpin dunia baru aja ngumumin sesuatu yang seharusnya bikin semua orang panik"
            </div>
            <div style={{ marginTop: "12px", fontSize: "0.8rem", color: "var(--text-secondary)" }}>
              Formula: <strong style={{ color: "var(--text-primary)" }}>[Otoritas] + [Aksi Besar] + [Konsekuensi menakutkan tanpa jawaban]</strong>
            </div>
            <div style={{ marginTop: "8px", fontSize: "0.8rem", color: "var(--text-muted)" }}>
              ✅ Bitcoin & New World Order (2 part) · ~900K views · Watch time 42% peak
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

export default function AnalyticsPage() {
  return (
    <ToastProvider>
      <AnalyticsContent />
    </ToastProvider>
  );
}
