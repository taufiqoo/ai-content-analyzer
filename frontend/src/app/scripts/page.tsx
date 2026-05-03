"use client";
import { useState, useEffect, useCallback } from "react";
import Sidebar from "@/components/Sidebar";
import { ToastProvider, useToast } from "@/components/Toast";
import { scriptsApi } from "@/lib/api";

const ANGLE_LABELS: Record<string, string> = {
  hero: "Hero",
  tips_trick: "Tips & Trick",
  controversial: "Controversial",
  storytelling: "Storytelling",
  reply_komen: "Reply Komentar",
};

function ScriptModal({ script, onClose, onUpdate }: { script: any; onClose: () => void; onUpdate: (s: any) => void }) {
  const { addToast } = useToast();
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState({ hook: script.hook, body: script.body, cta: script.cta });
  const [perfForm, setPerfForm] = useState({ views: "", likes: "", comments: "", shares: "", watch_time_percent: "", did_fyp: false, notes: "" });
  const [showPerfForm, setShowPerfForm] = useState(false);
  const [saving, setSaving] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(script.full_script);
    addToast("success", "Script copied to clipboard!");
  };

  const handleApprove = async () => {
    const updated = await scriptsApi.update(script.id, { status: "approved" });
    onUpdate(updated);
    addToast("success", "Script approved! ✅");
  };

  const handleReject = async () => {
    const updated = await scriptsApi.update(script.id, { status: "rejected" });
    onUpdate(updated);
    addToast("info", "Script rejected.");
  };

  const handleSaveEdit = async () => {
    setSaving(true);
    try {
      const updated = await scriptsApi.update(script.id, form);
      onUpdate(updated);
      setEditing(false);
      addToast("success", "Script saved!");
    } catch (e: any) {
      addToast("error", e.message);
    } finally {
      setSaving(false);
    }
  };

  const handleLogPerformance = async () => {
    try {
      await scriptsApi.logPerformance(script.id, {
        views: Number(perfForm.views) || 0,
        likes: Number(perfForm.likes) || 0,
        comments: Number(perfForm.comments) || 0,
        shares: Number(perfForm.shares) || 0,
        watch_time_percent: perfForm.watch_time_percent ? Number(perfForm.watch_time_percent) : null,
        did_fyp: perfForm.did_fyp,
        notes: perfForm.notes,
      });
      setShowPerfForm(false);
      addToast("success", "Performance logged! 📊");
    } catch (e: any) {
      addToast("error", e.message);
    }
  };

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div>
            <div className="modal-title">Script Detail</div>
            <div style={{ display: "flex", gap: "8px", marginTop: "8px", flexWrap: "wrap" }}>
              <span className={`badge badge-${script.status}`}>{script.status}</span>
              {script.angle && <span className={`badge badge-${script.angle}`}>{ANGLE_LABELS[script.angle] || script.angle}</span>}
              {script.hook_formula_used && <span className="badge badge-draft" style={{ fontSize: "0.65rem" }}>Formula: {script.hook_formula_used}</span>}
            </div>
          </div>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>

        {/* Naturalness score */}
        {script.naturalness_score && (
          <div style={{ marginBottom: "20px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "6px" }}>
              <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.08em" }}>Naturalness Score</span>
              <span style={{ fontSize: "0.8rem", color: "var(--text-primary)", fontWeight: 600 }}>{script.naturalness_score}/10</span>
            </div>
            <div className="naturalness-track">
              <div className="naturalness-fill" style={{ width: `${script.naturalness_score * 10}%` }} />
            </div>
          </div>
        )}

        {editing ? (
          <div>
            <div className="form-group">
              <label className="form-label">🎣 Hook</label>
              <textarea className="form-control" value={form.hook} onChange={(e) => setForm({ ...form, hook: e.target.value })} rows={3} />
            </div>
            <div className="form-group">
              <label className="form-label">📖 Body</label>
              <textarea className="form-control" value={form.body} onChange={(e) => setForm({ ...form, body: e.target.value })} rows={10} />
            </div>
            <div className="form-group">
              <label className="form-label">📣 CTA</label>
              <textarea className="form-control" value={form.cta} onChange={(e) => setForm({ ...form, cta: e.target.value })} rows={3} />
            </div>
            <div style={{ display: "flex", gap: "8px", justifyContent: "flex-end" }}>
              <button className="btn btn-ghost btn-sm" onClick={() => setEditing(false)}>Cancel</button>
              <button className="btn btn-primary btn-sm" onClick={handleSaveEdit} disabled={saving}>{saving ? "Saving..." : "Save Changes"}</button>
            </div>
          </div>
        ) : (
          <>
            <div className="script-section">
              <div className="script-section-label">🎣 Hook (Detik 0-5)</div>
              <div className="script-section-content hook">{script.hook}</div>
            </div>
            <hr className="divider" />
            <div className="script-section">
              <div className="script-section-label">📖 Body (Detik 5-50)</div>
              <div className="script-section-content">{script.body}</div>
            </div>
            <hr className="divider" />
            <div className="script-section">
              <div className="script-section-label">📣 CTA (Detik 50-60)</div>
              <div className="script-section-content">{script.cta}</div>
            </div>
            {script.duration_estimate && (
              <p style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "8px" }}>
                ⏱ Estimasi durasi: ~{script.duration_estimate} detik
              </p>
            )}
          </>
        )}

        {/* Performance form */}
        {showPerfForm && (
          <div style={{ marginTop: "20px", padding: "16px", background: "var(--bg-elevated)", borderRadius: "var(--radius-md)", border: "1px solid var(--border-subtle)" }}>
            <div className="card-title" style={{ marginBottom: "12px" }}>📊 Log Performance</div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
              {["views", "likes", "comments", "shares"].map((f) => (
                <div key={f} className="form-group" style={{ marginBottom: 0 }}>
                  <label className="form-label">{f}</label>
                  <input type="number" className="form-control" value={(perfForm as any)[f]} onChange={(e) => setPerfForm({ ...perfForm, [f]: e.target.value })} />
                </div>
              ))}
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px", marginTop: "12px" }}>
              <div className="form-group" style={{ marginBottom: 0 }}>
                <label className="form-label">Watch Time %</label>
                <input type="number" className="form-control" value={perfForm.watch_time_percent} onChange={(e) => setPerfForm({ ...perfForm, watch_time_percent: e.target.value })} />
              </div>
              <div className="form-group" style={{ marginBottom: 0 }}>
                <label className="form-label">FYP? 🚀</label>
                <select className="form-control" value={perfForm.did_fyp ? "true" : "false"} onChange={(e) => setPerfForm({ ...perfForm, did_fyp: e.target.value === "true" })}>
                  <option value="false">Tidak</option>
                  <option value="true">Ya, FYP!</option>
                </select>
              </div>
            </div>
            <div className="form-group" style={{ marginTop: "12px", marginBottom: "12px" }}>
              <label className="form-label">Notes</label>
              <textarea className="form-control" rows={2} value={perfForm.notes} onChange={(e) => setPerfForm({ ...perfForm, notes: e.target.value })} />
            </div>
            <div style={{ display: "flex", gap: "8px", justifyContent: "flex-end" }}>
              <button className="btn btn-ghost btn-sm" onClick={() => setShowPerfForm(false)}>Cancel</button>
              <button className="btn btn-success btn-sm" onClick={handleLogPerformance}>Save Performance</button>
            </div>
          </div>
        )}

        {/* Actions */}
        <div style={{ display: "flex", gap: "8px", marginTop: "20px", flexWrap: "wrap" }}>
          <button className="btn btn-primary btn-sm" onClick={handleCopy}>📋 Copy Script</button>
          {!editing && <button className="btn btn-secondary btn-sm" onClick={() => setEditing(true)}>✏️ Edit</button>}
          {script.status !== "approved" && <button className="btn btn-success btn-sm" onClick={handleApprove}>✅ Approve</button>}
          {script.status !== "rejected" && <button className="btn btn-danger btn-sm" onClick={handleReject}>❌ Reject</button>}
          <button className="btn btn-ghost btn-sm" onClick={() => setShowPerfForm(!showPerfForm)}>📊 Log Performance</button>
        </div>
      </div>
    </div>
  );
}

function ScriptsContent() {
  const [scripts, setScripts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("all");
  const [selectedScript, setSelectedScript] = useState<any>(null);
  const { addToast } = useToast();

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await scriptsApi.list({ status: filter === "all" ? undefined : filter });
      setScripts(data);
    } catch (e: any) {
      addToast("error", "Failed to load scripts");
    } finally {
      setLoading(false);
    }
  }, [filter]);

  useEffect(() => { load(); }, [load]);

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this script?")) return;
    await scriptsApi.delete(id);
    setScripts((prev) => prev.filter((s) => s.id !== id));
    addToast("success", "Script deleted");
  };

  const handleUpdate = (updated: any) => {
    setScripts((prev) => prev.map((s) => (s.id === updated.id ? updated : s)));
    setSelectedScript(updated);
  };

  const FILTERS = ["all", "draft", "approved", "rejected"];

  return (
    <div className="app-shell">
      <Sidebar />
      <main className="main-content">
        <div className="page-header">
          <h2 className="page-title">📝 Script Manager</h2>
          <p className="page-subtitle">{scripts.length} scripts · Review, edit, and approve your generated content</p>
        </div>

        <div className="tabs">
          {FILTERS.map((f) => (
            <button key={f} className={`tab ${filter === f ? "active" : ""}`} onClick={() => setFilter(f)}>
              {f.charAt(0).toUpperCase() + f.slice(1)}
              {f !== "all" && (
                <span style={{ marginLeft: "6px", opacity: 0.6, fontSize: "0.72rem" }}>
                  ({scripts.filter((s) => s.status === f).length || (f === filter ? scripts.length : 0)})
                </span>
              )}
            </button>
          ))}
        </div>

        {loading ? (
          <div className="empty-state">
            <div className="empty-state-icon">⏳</div>
            <div className="empty-state-title">Loading scripts...</div>
          </div>
        ) : scripts.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">📭</div>
            <div className="empty-state-title">No scripts found</div>
            <div className="empty-state-desc">Run the pipeline from the Dashboard or use Manual Generate to create scripts.</div>
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            {scripts.map((script) => (
              <div key={script.id} className={`script-card ${script.status}`} onClick={() => setSelectedScript(script)}>
                <div className="script-meta">
                  <span className={`badge badge-${script.status}`}>{script.status}</span>
                  {script.angle && <span className={`badge badge-${script.angle}`}>{ANGLE_LABELS[script.angle] || script.angle}</span>}
                  {script.naturalness_score && (
                    <span style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}>
                      🧠 Natural: {script.naturalness_score}/10
                    </span>
                  )}
                  {script.duration_estimate && (
                    <span style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}>
                      ⏱ ~{script.duration_estimate}s
                    </span>
                  )}
                </div>
                <div className="script-hook">{script.hook}</div>
                <div className="script-preview">{script.body}</div>
                <div className="script-actions" onClick={(e) => e.stopPropagation()}>
                  <button className="btn btn-primary btn-sm" onClick={() => { navigator.clipboard.writeText(script.full_script); addToast("success", "Copied!"); }}>
                    📋 Copy
                  </button>
                  <button className="btn btn-secondary btn-sm" onClick={() => setSelectedScript(script)}>
                    👁 View
                  </button>
                  {script.status !== "approved" && (
                    <button className="btn btn-success btn-sm" onClick={async () => {
                      const updated = await scriptsApi.update(script.id, { status: "approved" });
                      handleUpdate(updated);
                      addToast("success", "Approved!");
                    }}>
                      ✅ Approve
                    </button>
                  )}
                  <button className="btn btn-danger btn-sm" onClick={() => handleDelete(script.id)}>
                    🗑
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>

      {selectedScript && (
        <ScriptModal
          script={selectedScript}
          onClose={() => setSelectedScript(null)}
          onUpdate={handleUpdate}
        />
      )}
    </div>
  );
}

export default function ScriptsPage() {
  return (
    <ToastProvider>
      <ScriptsContent />
    </ToastProvider>
  );
}
