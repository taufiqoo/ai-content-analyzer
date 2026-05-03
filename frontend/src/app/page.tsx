"use client";
import { useState, useEffect, useCallback } from "react";
import Sidebar from "@/components/Sidebar";
import { ToastProvider, useToast } from "@/components/Toast";
import { jobsApi } from "@/lib/api";

function DashboardContent() {
  const { addToast } = useToast();
  const [summary, setSummary] = useState<any>(null);
  const [jobs, setJobs] = useState<any[]>([]);
  const [latestJob, setLatestJob] = useState<any>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [source, setSource] = useState("bookmarks");
  const [limit, setLimit] = useState(30);

  const fetchData = useCallback(async () => {
    try {
      const [s, j] = await Promise.all([jobsApi.getSummary(), jobsApi.listJobs()]);
      setSummary(s);
      setJobs(j);
      if (j.length > 0) setLatestJob(j[0]);
    } catch {}
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const handleRunPipeline = async () => {
    setIsRunning(true);
    try {
      const job = await jobsApi.trigger(source, limit);
      setLatestJob(job);
      addToast("success", "Pipeline started! Scraping Twitter...");
      fetchData();
    } catch (e: any) {
      addToast("error", e.message || "Failed to start pipeline");
    } finally {
      setIsRunning(false);
    }
  };

  const getStepState = (currentStep: string, targetStep: string) => {
    if (!latestJob || latestJob.status === "failed") return "waiting";
    const steps = ["queued", "scraping", "extracting_articles", "scoring_relevance", "generating_scripts", "done"];
    const ci = steps.indexOf(currentStep || "");
    const ti = steps.indexOf(targetStep);
    if (latestJob.status === "completed") return "done";
    if (ci > ti) return "done";
    if (ci === ti) return "running";
    return "waiting";
  };

  const STEPS = [
    { key: "scraping", label: "Scraping Twitter Bookmarks" },
    { key: "extracting_articles", label: "Extracting Articles" },
    { key: "scoring_relevance", label: "Scoring Relevance (Claude AI)" },
    { key: "generating_scripts", label: "Generating Scripts (Claude AI)" },
    { key: "done", label: "Pipeline Complete" },
  ];

  const stepProgress = latestJob
    ? latestJob.status === "completed"
      ? 100
      : (["scraping", "extracting_articles", "scoring_relevance", "generating_scripts", "done"].indexOf(latestJob.step) + 1) / 5 * 100
    : 0;

  return (
    <div className="app-shell">
      <Sidebar />
      <main className="main-content">
        <div className="page-header">
          <h2 className="page-title">Dashboard</h2>
          <p className="page-subtitle">Monitor your content automation pipeline</p>
        </div>

        {/* Stats */}
        <div className="stats-grid">
          {[
            { label: "Tweets Fetched", value: summary?.tweets_total ?? "—", icon: "🐦" },
            { label: "Relevant Content", value: summary?.tweets_relevant ?? "—", icon: "✅" },
            { label: "Scripts Generated", value: summary?.scripts_total ?? "—", icon: "📝" },
            { label: "Approved Scripts", value: summary?.scripts_approved ?? "—", icon: "🎬" },
            { label: "FYP Count", value: summary?.fyp_count ?? "—", icon: "🚀" },
            { label: "Total Views", value: summary?.total_views ? `${(summary.total_views / 1000).toFixed(0)}K` : "—", icon: "👁️" },
          ].map((s) => (
            <div key={s.label} className="stat-card">
              <div style={{ fontSize: "1.5rem", marginBottom: "8px" }}>{s.icon}</div>
              <div className="stat-value">{s.value}</div>
              <div className="stat-label">{s.label}</div>
            </div>
          ))}
        </div>

        {/* Run Pipeline */}
        <div className="grid-2">
          <div className="card">
            <div className="card-header">
              <div>
                <div className="card-title">🚀 Run Pipeline</div>
                <div className="card-subtitle">Scrape → Filter → Generate scripts automatically</div>
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Source</label>
              <select
                className="form-control"
                value={source}
                onChange={(e) => setSource(e.target.value)}
                style={{ cursor: "pointer" }}
              >
                <option value="bookmarks">Twitter Bookmarks</option>
                <option value="timeline">Home Timeline (FYP)</option>
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Max Tweets to Fetch</label>
              <input
                type="number"
                className="form-control"
                value={limit}
                min={5}
                max={100}
                onChange={(e) => setLimit(Number(e.target.value))}
              />
            </div>

            <button
              className="btn btn-primary btn-lg w-full"
              onClick={handleRunPipeline}
              disabled={isRunning}
            >
              {isRunning ? "⏳ Starting..." : "⚡ Run Full Pipeline"}
            </button>
          </div>

          {/* Pipeline Status */}
          <div className="card">
            <div className="card-header">
              <div>
                <div className="card-title">📡 Pipeline Status</div>
                {latestJob && (
                  <div className="card-subtitle">
                    {latestJob.status === "completed" && `✅ ${latestJob.scripts_generated} scripts generated`}
                    {latestJob.status === "running" && `⏳ Running: ${latestJob.step?.replace(/_/g, " ")}`}
                    {latestJob.status === "failed" && `❌ ${latestJob.error_message}`}
                  </div>
                )}
              </div>
              {latestJob && (
                <span className={`badge badge-${latestJob.status === "completed" ? "approved" : latestJob.status === "failed" ? "rejected" : "pending"}`}>
                  {latestJob.status}
                </span>
              )}
            </div>

            {latestJob ? (
              <>
                <div className="progress-bar" style={{ marginBottom: "20px" }}>
                  <div className="progress-fill" style={{ width: `${stepProgress}%` }} />
                </div>

                {STEPS.map((step) => {
                  const state = getStepState(latestJob?.step, step.key);
                  return (
                    <div key={step.key} className="pipeline-step">
                      <div className={`step-indicator ${state}`}>
                        {state === "done" ? "✓" : state === "running" ? "⋯" : "○"}
                      </div>
                      <span style={{ fontSize: "0.85rem", color: state === "done" ? "var(--success)" : state === "running" ? "var(--warning)" : "var(--text-muted)" }}>
                        {step.label}
                      </span>
                    </div>
                  );
                })}

                {latestJob.status === "completed" && (
                  <div style={{ marginTop: "16px", padding: "12px", background: "var(--success-dim)", borderRadius: "var(--radius-md)", fontSize: "0.85rem", color: "var(--success)" }}>
                    🎉 Fetched {latestJob.tweets_fetched} tweets · {latestJob.tweets_relevant} relevant · {latestJob.scripts_generated} scripts
                  </div>
                )}
              </>
            ) : (
              <div className="empty-state" style={{ padding: "40px 0" }}>
                <div className="empty-state-icon">🤖</div>
                <div className="empty-state-title">No pipeline runs yet</div>
                <div className="empty-state-desc">Click &quot;Run Full Pipeline&quot; to start automating your content creation.</div>
              </div>
            )}
          </div>
        </div>

        {/* Recent Jobs */}
        {jobs.length > 1 && (
          <div className="card mt-6">
            <div className="card-header">
              <div className="card-title">🕐 Recent Pipeline Runs</div>
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
              {jobs.slice(0, 5).map((job) => (
                <div key={job.id} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "12px 0", borderBottom: "1px solid var(--border-subtle)" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                    <span className={`badge badge-${job.status === "completed" ? "approved" : job.status === "failed" ? "rejected" : "pending"}`}>
                      {job.status}
                    </span>
                    <span style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>
                      {job.tweets_fetched} fetched · {job.tweets_relevant} relevant · {job.scripts_generated} scripts
                    </span>
                  </div>
                  <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                    {new Date(job.started_at).toLocaleString("id-ID")}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default function DashboardPage() {
  return (
    <ToastProvider>
      <DashboardContent />
    </ToastProvider>
  );
}
