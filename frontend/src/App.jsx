import { useEffect, useState } from "react";
import {
  addSource,
  generateNewsletter,
  ingestSource,
  listSources,
  sendNewsletter,
} from "./api/api";

const COLORS = {
  background: "#f5f5f4",
  surface: "#ffffff",
  border: "#e5e7eb",
  text: "#111827",
  muted: "#6b7280",
  accent: "#111827",
};

const pageStyle = {
  minHeight: "100vh",
  background: COLORS.background,
  padding: "48px 16px",
  color: COLORS.text,
  fontFamily: "Inter, system-ui, Arial",
};

const shellStyle = {
  maxWidth: "720px",
  margin: "0 auto",
  background: COLORS.surface,
  borderRadius: "20px",
  border: `1px solid ${COLORS.border}`,
  padding: "36px",
  display: "flex",
  flexDirection: "column",
  gap: "32px",
};

const headerStyle = {
  display: "flex",
  flexDirection: "column",
  gap: "0.6rem",
};

const headerBadgeStyle = {
  fontSize: "0.75rem",
  letterSpacing: "0.22em",
  textTransform: "uppercase",
  color: "#9ca3af",
};

const headerTitleStyle = {
  margin: 0,
  fontSize: "1.85rem",
  fontWeight: 600,
};

const headerSubtitleStyle = {
  margin: 0,
  color: COLORS.muted,
  fontSize: "1rem",
  lineHeight: 1.6,
};

const sectionStyle = {
  display: "flex",
  flexDirection: "column",
  gap: "1rem",
};

const sectionTitleStyle = {
  fontSize: "0.78rem",
  letterSpacing: "0.18em",
  textTransform: "uppercase",
  color: "#94a3b8",
};

const formStyle = {
  display: "flex",
  flexWrap: "wrap",
  gap: "0.75rem",
  alignItems: "center",
};

const inputStyle = {
  flex: "1 1 220px",
  padding: "0.65rem 0.85rem",
  borderRadius: "12px",
  border: `1px solid ${COLORS.border}`,
  background: "#f9fafb",
  fontSize: "0.95rem",
  color: COLORS.text,
};

const listStyle = {
  margin: 0,
  padding: 0,
  listStyle: "none",
  borderTop: `1px solid ${COLORS.border}`,
};

const listItemStyle = {
  display: "flex",
  flexWrap: "wrap",
  gap: "0.75rem",
  alignItems: "center",
  justifyContent: "space-between",
  padding: "0.9rem 0",
  borderBottom: `1px solid ${COLORS.border}`,
};

const sourceMetaStyle = {
  display: "flex",
  flexDirection: "column",
  gap: "0.25rem",
  minWidth: 0,
  flex: "1 1 260px",
};

const sourceNameStyle = {
  fontSize: "0.95rem",
  fontWeight: 500,
};

const sourceUrlStyle = {
  color: "#2563eb",
  fontSize: "0.9rem",
  textDecoration: "none",
  wordBreak: "break-word",
};

const buttonGroupStyle = {
  display: "flex",
  flexWrap: "wrap",
  gap: "0.6rem",
};

const previewStyle = {
  border: `1px solid ${COLORS.border}`,
  borderRadius: "16px",
  padding: "24px",
  background: "#fafafa",
  overflowX: "auto",
};

const emptyStateStyle = {
  border: `1px dashed ${COLORS.border}`,
  borderRadius: "12px",
  padding: "1rem",
  color: COLORS.muted,
  fontSize: "0.9rem",
  background: "#ffffff",
};

const noticeErrorStyle = {
  background: "#fee2e2",
  color: "#b91c1c",
  border: "1px solid #fecaca",
  borderRadius: "12px",
  padding: "0.75rem 1rem",
  fontSize: "0.9rem",
};

const noticeInfoStyle = {
  background: "#eef2ff",
  color: "#4338ca",
  borderRadius: "12px",
  padding: "0.6rem 1rem",
  fontSize: "0.85rem",
  width: "fit-content",
};

const buttonBaseStyle = {
  borderRadius: "999px",
  padding: "0.65rem 1.4rem",
  fontSize: "0.9rem",
  fontWeight: 500,
  border: "1px solid transparent",
  cursor: "pointer",
  transition: "background 0.2s ease, color 0.2s ease, border 0.2s ease, opacity 0.2s ease",
};

const buttonPrimaryStyle = {
  backgroundColor: COLORS.accent,
  color: "#ffffff",
};

const buttonSecondaryStyle = {
  backgroundColor: COLORS.surface,
  color: COLORS.text,
  border: `1px solid ${COLORS.border}`,
};

const buttonDisabledStyle = {
  opacity: 0.5,
  cursor: "not-allowed",
};

const getButtonStyle = (variant = "primary", disabled = false) => ({
  ...buttonBaseStyle,
  ...(variant === "primary" ? buttonPrimaryStyle : buttonSecondaryStyle),
  ...(disabled ? buttonDisabledStyle : {}),
});

function App() {
  const [draft, setDraft] = useState("");
  const [sources, setSources] = useState([]);
  const [newSourceName, setNewSourceName] = useState("");
  const [newSourceUrl, setNewSourceUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    handleLoadSources();
  }, []);

  const handleGenerate = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await generateNewsletter();
      setDraft(res.data.html || "");
    } catch (err) {
      setError("Failed to generate newsletter. Have you ingested any sources?");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSend = async () => {
    setLoading(true);
    setError("");
    try {
      await sendNewsletter();
      alert("Sent!");
    } catch (err) {
      setError("Failed to send newsletter.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleLoadSources = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await listSources();
      setSources(res.data || []);
    } catch (err) {
      setError("Failed to load sources.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleAddSource = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      await addSource(newSourceName, newSourceUrl);
      setNewSourceName("");
      setNewSourceUrl("");
      await handleLoadSources();
    } catch (err) {
      setError("Failed to add source. Does it already exist?");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleIngest = async (url) => {
    setLoading(true);
    setError("");
    try {
      const res = await ingestSource(url);
      alert(`Ingestion complete! ${res.data.inserted} new items added.`);
    } catch (err) {
      setError("Failed to ingest source.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={pageStyle}>
      <main style={shellStyle}>
        <header style={headerStyle}>
          <span style={headerBadgeStyle}>CreatorPulse</span>
          <h1 style={headerTitleStyle}>Daily briefing workspace</h1>
          <p style={headerSubtitleStyle}>
            Curate sources, generate summaries, and send polished updates from one minimal screen.
          </p>
        </header>

        {(error || loading) && (
          <div style={{ display: "flex", flexDirection: "column", gap: "0.6rem" }}>
            {error && <div style={noticeErrorStyle}>{error}</div>}
            {loading && <div style={noticeInfoStyle}>Working on it…</div>}
          </div>
        )}

        <section style={sectionStyle}>
          <span style={sectionTitleStyle}>Add source</span>
          <form onSubmit={handleAddSource} style={formStyle}>
            <input
              type="text"
              value={newSourceName}
              onChange={(e) => setNewSourceName(e.target.value)}
              placeholder="Source name"
              style={inputStyle}
              required
              disabled={loading}
            />
            <input
              type="url"
              value={newSourceUrl}
              onChange={(e) => setNewSourceUrl(e.target.value)}
              placeholder="RSS feed URL"
              style={inputStyle}
              required
              disabled={loading}
            />
            <button
              type="submit"
              style={getButtonStyle("primary", loading)}
              disabled={loading}
            >
              Add source
            </button>
          </form>
        </section>

        <section style={sectionStyle}>
          <span style={sectionTitleStyle}>Sources</span>
          {sources.length === 0 ? (
            <div style={emptyStateStyle}>
              No sources yet. Add one above to start building your briefing.
            </div>
          ) : (
            <ul style={listStyle}>
              {sources.map((s) => (
                <li key={s.id} style={listItemStyle}>
                  <div style={sourceMetaStyle}>
                    <span style={sourceNameStyle}>{s.name}</span>
                    <a
                      href={s.url}
                      target="_blank"
                      rel="noreferrer"
                      style={sourceUrlStyle}
                    >
                      {s.url}
                    </a>
                  </div>
                  <button
                    onClick={() => handleIngest(s.url)}
                    disabled={loading}
                    style={getButtonStyle("secondary", loading)}
                    title="Fetch new articles from this source"
                  >
                    Ingest
                  </button>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section style={sectionStyle}>
          <span style={sectionTitleStyle}>Newsletter</span>
          <div style={buttonGroupStyle}>
            <button
              onClick={handleGenerate}
              disabled={loading}
              style={getButtonStyle("secondary", loading)}
            >
              Generate draft
            </button>
            <button
              onClick={handleSend}
              disabled={loading || !draft}
              style={getButtonStyle("primary", loading || !draft)}
            >
              Send email
            </button>
          </div>

          {draft ? (
            <div style={previewStyle} dangerouslySetInnerHTML={{ __html: draft }} />
          ) : (
            <div style={emptyStateStyle}>
              Generate a draft to review the email layout here.
            </div>
          )}
        </section>
      </main>
    </div>
  );
}

export default App;
