"use client";
import { useState } from "react";
import Sidebar from "@/components/Sidebar";
import { ToastProvider, useToast } from "@/components/Toast";
import { scriptsApi, nicheApi } from "@/lib/api";
import { useEffect } from "react";

const ANGLE_LABELS: Record<string, string> = {
  hero: "Hero",
  tips_trick: "Tips & Trick",
  controversial: "Controversial",
  storytelling: "Storytelling",
  reply_komen: "Reply Komentar",
};

function ManualContent() {
  const { addToast } = useToast();
  const [content, setContent] = useState("");
  const [niches, setNiches] = useState<any[]>([]);
  const [selectedNiche, setSelectedNiche] = useState("");
  const [generating, setGenerating] = useState(false);
  const [scripts, setScripts] = useState<any[]>([]);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  useEffect(() => {
    nicheApi.list().then((n) => {
      setNiches(n);
      const active = n.find((x: any) => x.is_active);
      if (active) setSelectedNiche(active.id);
    }).catch(() => {});
  }, []);

  const handleGenerate = async () => {
    if (!content.trim() || content.length < 100) {
      addToast("error", "Artikel terlalu pendek (min 100 karakter)");
      return;
    }
    setGenerating(true);
    setScripts([]);
    try {
      const result = await scriptsApi.generateManual(content, selectedNiche || undefined);
      setScripts(result);
      addToast("success", `${result.length} scripts generated!`);
    } catch (e: any) {
      addToast("error", e.message || "Generation failed");
    } finally {
      setGenerating(false);
    }
  };

  const handleCopy = (script: any) => {
    navigator.clipboard.writeText(script.full_script);
    setCopiedId(script.id);
    setTimeout(() => setCopiedId(null), 2000);
    addToast("success", "Script copied!");
  };

  const handleApprove = async (script: any) => {
    try {
      await scriptsApi.update(script.id, { status: "approved" });
      setScripts((prev) => prev.map((s) => s.id === script.id ? { ...s, status: "approved" } : s));
      addToast("success", "Approved!");
    } catch {}
  };

  return (
    <div className="app-shell">
      <Sidebar />
      <main className="main-content">
        <div className="page-header">
          <h2 className="page-title">✍️ Manual Generate</h2>
          <p className="page-subtitle">Paste artikel atau konten dari mana saja — Claude akan generate multiple script angles</p>
        </div>

        <div className="grid-2" style={{ alignItems: "start" }}>
          {/* Input Panel */}
          <div className="card">
            <div className="card-header">
              <div className="card-title">📄 Input Konten</div>
            </div>

            <div className="form-group">
              <label className="form-label">Niche</label>
              <select className="form-control" value={selectedNiche} onChange={(e) => setSelectedNiche(e.target.value)}>
                <option value="">Auto (Default Active Niche)</option>
                {niches.map((n) => (
                  <option key={n.id} value={n.id}>{n.name}</option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">
                Paste Artikel / Konten
                <span style={{ marginLeft: "8px", color: "var(--text-muted)", fontWeight: 400, textTransform: "none" }}>
                  ({content.length} karakter)
                </span>
              </label>
              <textarea
                className="form-control"
                style={{ minHeight: "300px" }}
                placeholder="Paste artikel, thread Twitter, atau konten apapun di sini...

Contoh:
- Full artikel dari website
- Thread Twitter yang panjang
- Tulisan dari buku / podcast
- Apapun yang punya insight menarik untuk dijadikan konten TikTok

Minimal 100 karakter."
                value={content}
                onChange={(e) => setContent(e.target.value)}
              />
            </div>

            <button
              className="btn btn-primary btn-lg w-full"
              onClick={handleGenerate}
              disabled={generating || content.length < 100}
            >
              {generating ? (
                <>⏳ Generating {4} Scripts...</>
              ) : (
                <>🤖 Generate Scripts (4 Angles)</>
              )}
            </button>

            {generating && (
              <div style={{ marginTop: "12px" }}>
                <div className="progress-bar">
                  <div className="progress-fill" style={{ width: "100%" }} />
                </div>
                <p style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginTop: "8px", textAlign: "center" }}>
                  Claude is generating scripts... ~30 detik
                </p>
              </div>
            )}
          </div>

          {/* Generated Scripts */}
          <div>
            {scripts.length === 0 ? (
              <div className="card">
                <div className="empty-state" style={{ padding: "48px 0" }}>
                  <div className="empty-state-icon">🎬</div>
                  <div className="empty-state-title">Belum ada script</div>
                  <div className="empty-state-desc">
                    Paste artikel di sebelah kiri, lalu klik Generate. Claude akan buat 4 script dengan angle berbeda:
                    <br/><br/>
                    <strong style={{ color: "var(--text-primary)" }}>Hero · Tips &amp; Trick · Controversial · Storytelling</strong>
                  </div>
                </div>
              </div>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
                {scripts.map((script) => (
                  <div key={script.id} className="card">
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "12px" }}>
                      <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
                        <span className={`badge badge-${script.angle}`}>{ANGLE_LABELS[script.angle] || script.angle}</span>
                        <span className={`badge badge-${script.status}`}>{script.status}</span>
                        {script.naturalness_score && (
                          <span style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}>
                            🧠 {script.naturalness_score}/10
                          </span>
                        )}
                      </div>
                      {script.duration_estimate && (
                        <span style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}>⏱ ~{script.duration_estimate}s</span>
                      )}
                    </div>

                    {/* Hook highlighted */}
                    <div style={{
                      background: "var(--accent-dim)",
                      border: "1px solid var(--border)",
                      borderRadius: "var(--radius-md)",
                      padding: "12px 16px",
                      marginBottom: "12px",
                      fontSize: "0.9rem",
                      fontWeight: 600,
                      color: "var(--text-primary)",
                      lineHeight: 1.5,
                    }}>
                      🎣 {script.hook}
                    </div>

                    <div style={{ fontSize: "0.85rem", color: "var(--text-secondary)", lineHeight: 1.7, marginBottom: "12px", display: "-webkit-box", WebkitLineClamp: 4, WebkitBoxOrient: "vertical", overflow: "hidden" }}>
                      {script.body}
                    </div>

                    <div style={{ fontSize: "0.85rem", color: "var(--text-muted)", borderTop: "1px solid var(--border-subtle)", paddingTop: "12px" }}>
                      📣 {script.cta}
                    </div>

                    {script.hook_formula_used && (
                      <div style={{ fontSize: "0.72rem", color: "var(--text-muted)", marginTop: "8px" }}>
                        Formula: {script.hook_formula_used}
                      </div>
                    )}

                    <div style={{ display: "flex", gap: "8px", marginTop: "16px" }}>
                      <button className="btn btn-primary btn-sm" onClick={() => handleCopy(script)}>
                        {copiedId === script.id ? "✓ Copied!" : "📋 Copy Full Script"}
                      </button>
                      {script.status !== "approved" && (
                        <button className="btn btn-success btn-sm" onClick={() => handleApprove(script)}>
                          ✅ Approve
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

export default function ManualPage() {
  return (
    <ToastProvider>
      <ManualContent />
    </ToastProvider>
  );
}
