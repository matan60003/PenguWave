import { useState } from "react";
import { createEvent } from "../api";
import { SecurityEvent } from "../types";

interface Props {
  onClose: () => void;
  onCreated: (event: SecurityEvent) => void;
}

export default function CreateEventModal({ onClose, onCreated }: Props) {
  const [title, setTitle] = useState("");
  const [severity, setSeverity] = useState<"HIGH" | "MEDIUM" | "LOW">("LOW");
  const [description, setDescription] = useState("");
  const [assetHostname, setAssetHostname] = useState("");
  const [assetIp, setAssetIp] = useState("10.0.0.1");
  const [sourceIp, setSourceIp] = useState("192.168.1.1");
  const [tags, setTags] = useState("manual, created");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const newEvent = await createEvent({
        title,
        severity,
        description,
        assetHostname,
        assetIp,
        sourceIp,
        tags: tags.split(",").map(t => t.trim()),
        userId: "system",
      });
      onCreated(newEvent);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to create event");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-backdrop">
      <div className="modal-content" style={{ maxWidth: 500 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
          <h2 style={{ margin: 0 }}>Create Security Event</h2>
          <button onClick={onClose} style={{ background: "none", border: "none", fontSize: 24, cursor: "pointer", lineHeight: 1 }}>&times;</button>
        </div>
        {error && <div style={{ color: "red", marginBottom: 16 }}>{error}</div>}
        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          <div>
            <label style={{ display: "block", marginBottom: 4, fontWeight: "bold", fontSize: 14 }}>Title</label>
            <input required type="text" value={title} onChange={e => setTitle(e.target.value)} style={{ width: "100%", padding: 8, boxSizing: "border-box" }} />
          </div>
          <div>
            <label style={{ display: "block", marginBottom: 4, fontWeight: "bold", fontSize: 14 }}>Severity</label>
            <select value={severity} onChange={e => setSeverity(e.target.value as "HIGH" | "MEDIUM" | "LOW")} style={{ width: "100%", padding: 8, boxSizing: "border-box" }}>
              <option value="LOW">LOW</option>
              <option value="MEDIUM">MEDIUM</option>
              <option value="HIGH">HIGH</option>
            </select>
          </div>
          <div>
            <label style={{ display: "block", marginBottom: 4, fontWeight: "bold", fontSize: 14 }}>Asset Hostname</label>
            <input required type="text" value={assetHostname} onChange={e => setAssetHostname(e.target.value)} style={{ width: "100%", padding: 8, boxSizing: "border-box" }} />
          </div>
          <div style={{ display: "flex", gap: 8 }}>
            <div style={{ flex: 1 }}>
              <label style={{ display: "block", marginBottom: 4, fontWeight: "bold", fontSize: 14 }}>Asset IP</label>
              <input required type="text" value={assetIp} onChange={e => setAssetIp(e.target.value)} style={{ width: "100%", padding: 8, boxSizing: "border-box" }} />
            </div>
            <div style={{ flex: 1 }}>
              <label style={{ display: "block", marginBottom: 4, fontWeight: "bold", fontSize: 14 }}>Source IP</label>
              <input required type="text" value={sourceIp} onChange={e => setSourceIp(e.target.value)} style={{ width: "100%", padding: 8, boxSizing: "border-box" }} />
            </div>
          </div>
          <div>
            <label style={{ display: "block", marginBottom: 4, fontWeight: "bold", fontSize: 14 }}>Tags (comma separated)</label>
            <input required type="text" value={tags} onChange={e => setTags(e.target.value)} style={{ width: "100%", padding: 8, boxSizing: "border-box" }} />
          </div>
          <div>
            <label style={{ display: "block", marginBottom: 4, fontWeight: "bold", fontSize: 14 }}>Description</label>
            <textarea required value={description} onChange={e => setDescription(e.target.value)} rows={3} style={{ width: "100%", padding: 8, boxSizing: "border-box", fontFamily: "inherit" }}></textarea>
          </div>
          <button type="submit" className="btn-primary" disabled={loading} style={{ padding: 12, marginTop: 8 }}>
            {loading ? "Creating..." : "Create Event"}
          </button>
        </form>
      </div>
    </div>
  );
}
