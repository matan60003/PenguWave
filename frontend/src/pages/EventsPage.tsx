import { useState, useEffect } from "react";
import { getEvents, deleteEvent } from "../api";
import { SecurityEvent } from "../types";
import { useAuth } from "../context/AuthContext";
import CreateEventModal from "../components/CreateEventModal";

export default function EventsPage() {
  const [search, setSearch] = useState("");
  const [severityFilter, setSeverityFilter] = useState("ALL");
  const [selectedEvent, setSelectedEvent] = useState<SecurityEvent | null>(null);
  const [events, setEvents] = useState<SecurityEvent[]>([]);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [showModal, setShowModal] = useState(false);
  const { user } = useAuth();
  const isAdmin = user?.role === "admin";
  const limit = 25;

  useEffect(() => {
    const timeout = setTimeout(() => {
      getEvents(page, limit, search, severityFilter)
        .then(res => {
          setEvents(res.data);
          setTotal(res.total);
        })
        .catch(err => console.error("Failed to fetch events:", err));
    }, 300);
    return () => clearTimeout(timeout);
  }, [page, search, severityFilter]);

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await deleteEvent(id);
      setEvents(prev => prev.filter(evt => evt.id !== id));
      if (selectedEvent?.id === id) setSelectedEvent(null);
    } catch (err: unknown) {
      alert("Failed to delete event: " + ((err instanceof Error && err.message) || "Unknown error"));
    }
  };

  const severityColor = (s: string) => {
    if (s === "HIGH") return "red";
    if (s === "MEDIUM") return "orange";
    return "green";
  };

  return (
    <div className="page-container">
      <h1>Security Events</h1>

      <div style={{ marginBottom: 16, display: "flex", gap: 12, alignItems: "center" }}>
        <input
          type="text"
          placeholder="Search events..."
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(1); }}
          style={{ width: "100%", maxWidth: 400 }}
        />
        <select
          value={severityFilter}
          onChange={(e) => { setSeverityFilter(e.target.value); setPage(1); }}
          style={{ width: 140 }}
        >
          <option value="ALL">All Severities</option>
          <option value="HIGH">High</option>
          <option value="MEDIUM">Medium</option>
          <option value="LOW">Low</option>
        </select>
        {isAdmin && (
          <button className="btn-primary" onClick={() => setShowModal(true)} style={{ marginLeft: "auto", padding: "8px 16px" }}>
            Create Event
          </button>
        )}
      </div>

      <table>
        <thead>
          <tr>
            <th>Severity</th>
            <th>Title</th>
            <th>Asset</th>
            <th>Source IP</th>
            <th>Timestamp</th>
            {isAdmin && <th>Actions</th>}
          </tr>
        </thead>
        <tbody>
          {events.map((event) => (
            <tr
              key={event.id}
              onClick={() => setSelectedEvent(event)}
              style={{ cursor: "pointer" }}
            >
              <td style={{ color: severityColor(event.severity), fontWeight: 600 }}>
                {event.severity}
              </td>
              <td>{event.title}</td>
              <td style={{ fontFamily: "monospace", fontSize: 13 }}>
                {event.assetHostname}
              </td>
              <td style={{ fontFamily: "monospace", fontSize: 13 }}>
                {event.sourceIp}
              </td>
              <td style={{ fontSize: 13 }}>
                {new Date(event.timestamp).toLocaleString()}
              </td>
              {isAdmin && (
                <td>
                  <button 
                    onClick={(e) => handleDelete(event.id, e)}
                    style={{ background: "transparent", color: "red", border: "1px solid red", padding: "4px 8px", cursor: "pointer" }}
                  >
                    Delete
                  </button>
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>

      {events.length === 0 && <p style={{ color: "#999" }}>No events found.</p>}

      <div style={{ marginTop: 16, display: "flex", gap: 8, alignItems: "center" }}>
        <button 
          disabled={page === 1} 
          onClick={() => setPage(page - 1)}
          style={{ padding: "4px 8px" }}
        >
          Previous
        </button>
        <span style={{ fontSize: 14 }}>Page {page} of {Math.ceil(total / limit) || 1}</span>
        <button 
          disabled={page >= Math.ceil(total / limit) || total === 0} 
          onClick={() => setPage(page + 1)}
          style={{ padding: "4px 8px" }}
        >
          Next
        </button>
        <span style={{ marginLeft: "auto", color: "#666", fontSize: 13 }}>
          Total Events: {total}
        </span>
      </div>

      <div style={{ marginTop: 12 }}>
        <button
          onClick={() => {
            const blob = new Blob([JSON.stringify(events, null, 2)], { type: "application/json" });
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = "penguwave_events_export.json";
            a.click();
            setTimeout(() => URL.revokeObjectURL(url), 100);
          }}
          style={{ fontSize: 13 }}
        >
          Export Current Page (JSON)
        </button>
      </div>

      {/* Inline event detail */}
      {selectedEvent && (
        <div className="event-detail">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <h2>{selectedEvent.title}</h2>
            <button onClick={() => setSelectedEvent(null)} style={{ cursor: "pointer" }}>
              Close
            </button>
          </div>
          <p>
            <strong>Severity:</strong>{" "}
            <span style={{ color: severityColor(selectedEvent.severity) }}>
              {selectedEvent.severity}
            </span>
          </p>
          <p>
            <strong>Description:</strong>
          </p>
          <div>{selectedEvent.description}</div>
          <p>
            <strong>Asset:</strong> {selectedEvent.assetHostname} ({selectedEvent.assetIp})
          </p>
          <p>
            <strong>Source IP:</strong> {selectedEvent.sourceIp}
          </p>
          <p>
            <strong>Tags:</strong> {selectedEvent.tags.join(", ")}
          </p>
          <p>
            <strong>Timestamp:</strong> {new Date(selectedEvent.timestamp).toLocaleString()}
          </p>
          <h3>Raw Event Data</h3>
          <pre>{JSON.stringify(selectedEvent, null, 2)}</pre>
        </div>
      )}

      {showModal && (
        <CreateEventModal
          onClose={() => setShowModal(false)}
          onCreated={(newEvent) => {
            // Ideally re-fetch or optimistically add
            getEvents(page, limit, search, severityFilter).then(res => {
              setEvents(res.data);
              setTotal(res.total);
            });
            setShowModal(false);
          }}
        />
      )}
    </div>
  );
}
