"use client";
import { useState, useEffect } from "react";
import Sidebar from "@/components/Sidebar";
import { ToastProvider, useToast } from "@/components/Toast";
import { tweetsApi } from "@/lib/api";

function TweetsContent() {
  const [tweets, setTweets] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("all");
  const { addToast } = useToast();

  useEffect(() => {
    setLoading(true);
    tweetsApi.list({ status: filter === "all" ? undefined : filter })
      .then(setTweets)
      .catch(() => addToast("error", "Failed to load tweets"))
      .finally(() => setLoading(false));
  }, [filter]);

  const FILTERS = ["all", "pending", "relevant", "irrelevant", "scripted"];

  const statusColor: Record<string, string> = {
    pending: "var(--warning)",
    relevant: "var(--success)",
    irrelevant: "var(--danger)",
    scripted: "var(--info)",
  };

  return (
    <div className="app-shell">
      <Sidebar />
      <main className="main-content">
        <div className="page-header">
          <h2 className="page-title">🐦 Tweet Sources</h2>
          <p className="page-subtitle">{tweets.length} tweets · Content scraped from Twitter</p>
        </div>

        <div className="tabs">
          {FILTERS.map((f) => (
            <button key={f} className={`tab ${filter === f ? "active" : ""}`} onClick={() => setFilter(f)}>
              {f.charAt(0).toUpperCase() + f.slice(1)}
            </button>
          ))}
        </div>

        {loading ? (
          <div className="empty-state"><div className="empty-state-icon">⏳</div><div className="empty-state-title">Loading...</div></div>
        ) : tweets.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">📭</div>
            <div className="empty-state-title">No tweets found</div>
            <div className="empty-state-desc">Run the pipeline from the Dashboard to fetch tweets from your Twitter bookmarks.</div>
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
            {tweets.map((tweet) => (
              <div key={tweet.id} className="card" style={{ padding: "16px 20px" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "8px" }}>
                      <span className={`badge badge-${tweet.status}`}>{tweet.status}</span>
                      {tweet.has_article_link && <span className="badge badge-draft">📰 Has Article</span>}
                      {tweet.author_username && (
                        <span style={{ fontSize: "0.78rem", color: "var(--text-muted)" }}>@{tweet.author_username}</span>
                      )}
                    </div>
                    <p style={{ fontSize: "0.875rem", color: "var(--text-primary)", lineHeight: 1.5, marginBottom: "8px" }}>
                      {tweet.content?.slice(0, 280)}
                      {(tweet.content?.length || 0) > 280 && "..."}
                    </p>
                    {tweet.relevance_score !== null && tweet.relevance_score !== undefined && (
                      <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                        <div style={{ width: "80px", height: "4px", background: "var(--bg-elevated)", borderRadius: "9999px", overflow: "hidden" }}>
                          <div style={{ width: `${tweet.relevance_score * 100}%`, height: "100%", background: tweet.relevance_score >= 0.65 ? "var(--success)" : "var(--danger)", borderRadius: "9999px" }} />
                        </div>
                        <span style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}>
                          Relevance: {(tweet.relevance_score * 100).toFixed(0)}%
                        </span>
                        {tweet.relevance_reason && (
                          <span style={{ fontSize: "0.72rem", color: "var(--text-muted)", fontStyle: "italic" }}>
                            · {tweet.relevance_reason}
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                  {tweet.url && (
                    <a href={tweet.url} target="_blank" rel="noopener noreferrer" className="btn btn-ghost btn-sm" style={{ marginLeft: "12px", flexShrink: 0 }}>
                      🔗 View
                    </a>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}

export default function TweetsPage() {
  return (
    <ToastProvider>
      <TweetsContent />
    </ToastProvider>
  );
}
