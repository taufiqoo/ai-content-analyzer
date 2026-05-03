"use client";
import { useState, useEffect } from "react";
import Sidebar from "@/components/Sidebar";
import { ToastProvider, useToast } from "@/components/Toast";
import { nicheApi } from "@/lib/api";

const DEFAULT_HOOKS = [
  '[Figur/institusi besar] baru aja [aksi besar] — dan [konsekuensi menakutkan]',
  'Jangan bilang lo udah [X] kalo lo masih [Y]',
  'Semua orang SALAH soal [topik]',
  'Jangan heran kenapa [X] — karena [Y]',
  'Ini alasan kenapa [X] — dan nggak ada yang berani bilang',
  'GILA. Kenapa nggak ada yang bilang dari dulu kalo [X]',
  'Ngaku deh — lo sering ngerasain [X]',
  'Jangan pernah berani-berani [X]',
  'Lo pikir [X] — tapi yang terjadi justru sebaliknya',
  'Ada yang lagi terjadi sekarang — dan hampir nggak ada yang ngomongin ini',
];

function NicheModal({ niche, onClose, onSave }: { niche?: any; onClose: () => void; onSave: (data: any) => void }) {
  const { addToast } = useToast();
  const [form, setForm] = useState({
    name: niche?.name || "",
    keywords: (niche?.keywords || []).join(", "),
    hook_formulas: niche?.hook_formulas || [...DEFAULT_HOOKS],
    script_rules: niche?.script_rules || "",
    target_duration_seconds: niche?.target_duration_seconds || 60,
    is_active: niche?.is_active ?? true,
  });
  const [saving, setSaving] = useState(false);
  const [newHook, setNewHook] = useState("");

  const handleSave = async () => {
    if (!form.name.trim()) { addToast("error", "Name is required"); return; }
    setSaving(true);
    try {
      const data = {
        name: form.name,
        keywords: form.keywords.split(",").map((k: string) => k.trim()).filter(Boolean),
        hook_formulas: form.hook_formulas,
        script_rules: form.script_rules,
        target_duration_seconds: Number(form.target_duration_seconds),
        is_active: form.is_active,
      };
      let result;
      if (niche?.id) {
        result = await nicheApi.update(niche.id, data);
      } else {
        result = await nicheApi.create(data);
      }
      onSave(result);
      addToast("success", niche?.id ? "Niche updated!" : "Niche created!");
      onClose();
    } catch (e: any) {
      addToast("error", e.message);
    } finally {
      setSaving(false);
    }
  };

  const addHook = () => {
    if (!newHook.trim()) return;
    setForm((prev) => ({ ...prev, hook_formulas: [...prev.hook_formulas, newHook.trim()] }));
    setNewHook("");
  };

  const removeHook = (idx: number) => {
    setForm((prev) => ({ ...prev, hook_formulas: prev.hook_formulas.filter((_: any, i: number) => i !== idx) }));
  };

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-title">{niche?.id ? "Edit Niche" : "Create Niche"}</div>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>

        <div className="form-group">
          <label className="form-label">Niche Name *</label>
          <input className="form-control" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="e.g. Self-Development" />
        </div>

        <div className="form-group">
          <label className="form-label">Keywords (comma-separated)</label>
          <input className="form-control" value={form.keywords} onChange={(e) => setForm({ ...form, keywords: e.target.value })} placeholder="produktivitas, mindset, kebiasaan, buku" />
        </div>

        <div className="form-group">
          <label className="form-label">Target Duration (seconds)</label>
          <input type="number" className="form-control" value={form.target_duration_seconds} onChange={(e) => setForm({ ...form, target_duration_seconds: Number(e.target.value) })} min={30} max={180} />
        </div>

        <div className="form-group">
          <label className="form-label">Script Rules (optional)</label>
          <textarea className="form-control" rows={3} value={form.script_rules} onChange={(e) => setForm({ ...form, script_rules: e.target.value })} placeholder="Aturan tambahan khusus untuk niche ini..." />
        </div>

        <div className="form-group">
          <label className="form-label">Hook Formula Bank ({form.hook_formulas.length})</label>
          <div style={{ display: "flex", flexDirection: "column", gap: "6px", marginBottom: "8px", maxHeight: "200px", overflowY: "auto" }}>
            {form.hook_formulas.map((h: string, i: number) => (
              <div key={i} style={{ display: "flex", alignItems: "flex-start", gap: "8px", background: "var(--bg-elevated)", padding: "8px 12px", borderRadius: "var(--radius-md)", border: "1px solid var(--border-subtle)" }}>
                <span style={{ fontSize: "0.8rem", color: "var(--text-muted)", flexShrink: 0, marginTop: "2px" }}>{i + 1}.</span>
                <span style={{ fontSize: "0.8rem", color: "var(--text-primary)", flex: 1 }}>{h}</span>
                <button onClick={() => removeHook(i)} style={{ background: "none", border: "none", color: "var(--text-muted)", cursor: "pointer", fontSize: "0.9rem", flexShrink: 0 }}>✕</button>
              </div>
            ))}
          </div>
          <div style={{ display: "flex", gap: "8px" }}>
            <input className="form-control" value={newHook} onChange={(e) => setNewHook(e.target.value)} placeholder="Add new hook formula..." onKeyDown={(e) => e.key === "Enter" && addHook()} style={{ marginBottom: 0 }} />
            <button className="btn btn-secondary btn-sm" onClick={addHook} style={{ flexShrink: 0 }}>Add</button>
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "20px" }}>
          <input type="checkbox" id="is_active" checked={form.is_active} onChange={(e) => setForm({ ...form, is_active: e.target.checked })} />
          <label htmlFor="is_active" style={{ fontSize: "0.875rem", color: "var(--text-secondary)", cursor: "pointer" }}>Active (used in pipeline)</label>
        </div>

        <div style={{ display: "flex", gap: "8px", justifyContent: "flex-end" }}>
          <button className="btn btn-ghost" onClick={onClose}>Cancel</button>
          <button className="btn btn-primary" onClick={handleSave} disabled={saving}>{saving ? "Saving..." : niche?.id ? "Update Niche" : "Create Niche"}</button>
        </div>
      </div>
    </div>
  );
}

function SettingsContent() {
  const [niches, setNiches] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingNiche, setEditingNiche] = useState<any>(null);
  const [showModal, setShowModal] = useState(false);
  const { addToast } = useToast();

  useEffect(() => {
    nicheApi.list()
      .then(setNiches)
      .catch(() => addToast("error", "Failed to load niches"))
      .finally(() => setLoading(false));
  }, []);

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this niche config?")) return;
    await nicheApi.delete(id);
    setNiches((prev) => prev.filter((n) => n.id !== id));
    addToast("success", "Deleted");
  };

  const handleSave = (saved: any) => {
    setNiches((prev) => {
      const idx = prev.findIndex((n) => n.id === saved.id);
      if (idx >= 0) return prev.map((n) => n.id === saved.id ? saved : n);
      return [...prev, saved];
    });
  };

  return (
    <div className="app-shell">
      <Sidebar />
      <main className="main-content">
        <div className="page-header">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
            <div>
              <h2 className="page-title">⚙️ Settings</h2>
              <p className="page-subtitle">Manage your niche configs, hook formulas, and script rules</p>
            </div>
            <button className="btn btn-primary" onClick={() => { setEditingNiche(null); setShowModal(true); }}>
              + New Niche
            </button>
          </div>
        </div>

        {loading ? (
          <div className="empty-state"><div className="empty-state-icon">⏳</div></div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            {niches.map((niche) => (
              <div key={niche.id} className="card">
                <div className="card-header">
                  <div>
                    <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "4px" }}>
                      <div className="card-title">{niche.name}</div>
                      <span className={`badge badge-${niche.is_active ? "approved" : "rejected"}`}>
                        {niche.is_active ? "Active" : "Inactive"}
                      </span>
                    </div>
                    <div className="card-subtitle">⏱ {niche.target_duration_seconds}s · {niche.keywords?.length || 0} keywords · {niche.hook_formulas?.length || 0} hook formulas</div>
                  </div>
                  <div style={{ display: "flex", gap: "8px" }}>
                    <button className="btn btn-secondary btn-sm" onClick={() => { setEditingNiche(niche); setShowModal(true); }}>✏️ Edit</button>
                    <button className="btn btn-danger btn-sm" onClick={() => handleDelete(niche.id)}>🗑</button>
                  </div>
                </div>

                {niche.keywords?.length > 0 && (
                  <div style={{ display: "flex", flexWrap: "wrap", gap: "6px", marginBottom: "12px" }}>
                    {niche.keywords.map((k: string) => (
                      <span key={k} className="badge badge-draft">{k}</span>
                    ))}
                  </div>
                )}

                {niche.hook_formulas?.length > 0 && (
                  <div>
                    <div className="form-label" style={{ marginBottom: "6px" }}>Hook Formulas</div>
                    <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                      {niche.hook_formulas.slice(0, 3).map((h: string, i: number) => (
                        <div key={i} style={{ fontSize: "0.8rem", color: "var(--text-secondary)", padding: "6px 10px", background: "var(--bg-elevated)", borderRadius: "var(--radius-sm)" }}>
                          {i + 1}. {h}
                        </div>
                      ))}
                      {niche.hook_formulas.length > 3 && (
                        <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", padding: "4px 10px" }}>+{niche.hook_formulas.length - 3} more formulas</div>
                      )}
                    </div>
                  </div>
                )}

                {niche.script_rules && (
                  <div style={{ marginTop: "12px", fontSize: "0.8rem", color: "var(--text-secondary)", fontStyle: "italic" }}>
                    📋 {niche.script_rules}
                  </div>
                )}
              </div>
            ))}

            {niches.length === 0 && (
              <div className="empty-state">
                <div className="empty-state-icon">⚙️</div>
                <div className="empty-state-title">No niche configs</div>
                <div className="empty-state-desc">Create your first niche config to start generating targeted scripts. Or run the seeder to add 5 default niches.</div>
              </div>
            )}
          </div>
        )}
      </main>

      {showModal && (
        <NicheModal
          niche={editingNiche}
          onClose={() => setShowModal(false)}
          onSave={handleSave}
        />
      )}
    </div>
  );
}

export default function SettingsPage() {
  return (
    <ToastProvider>
      <SettingsContent />
    </ToastProvider>
  );
}
