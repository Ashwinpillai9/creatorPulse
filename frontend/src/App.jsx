import { useState, useEffect } from "react";
import { generateNewsletter, sendNewsletter, listSources, addSource, ingestSource } from "./api/api";

function App() {
  const [draft, setDraft] = useState("");
  const [sources, setSources] = useState([]);
  const [newSourceName, setNewSourceName] = useState("");
  const [newSourceUrl, setNewSourceUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Load sources on initial render
  useEffect(() => {
    handleLoadSources();
  }, []);

  const handleGenerate = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await generateNewsletter();
      setDraft(res.data.markdown);
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
      await handleLoadSources(); // Refresh the list
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
    <div style={{ maxWidth: 800, margin: "2rem auto", fontFamily: "Inter, system-ui, Arial", color: "#333" }}>
      <h1>CreatorPulse</h1>
      <p>Your AI assistant for curating and writing newsletters.</p>

      {error && <p style={{ color: "red" }}>{error}</p>}
      {loading && <p>Loading...</p>}

      <div style={{ background: "#f7f7f7", padding: "1rem", borderRadius: "8px", marginBottom: "2rem" }}>
        <h3>Add New Source</h3>
        <form onSubmit={handleAddSource} style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
          <input
            type="text"
            value={newSourceName}
            onChange={(e) => setNewSourceName(e.target.value)}
            placeholder="Source Name (e.g., TechCrunch)"
            style={{ flex: 1, padding: "0.5rem" }}
            required
          />
          <input
            type="url"
            value={newSourceUrl}
            onChange={(e) => setNewSourceUrl(e.target.value)}
            placeholder="RSS Feed URL"
            style={{ flex: 2, padding: "0.5rem" }}
            required
          />
          <button type="submit" disabled={loading}>Add</button>
        </form>
      </div>

      <div style={{ marginBottom: "2rem" }}>
        <h3>Sources</h3>
        <ul style={{ listStyle: "none", padding: 0 }}>
          {sources.map((s) => (
            <li key={s.id} style={{ display: "flex", alignItems: "center", gap: "1rem", marginBottom: "0.5rem" }}>
              <span>{s.name}</span>
              <a href={s.url} target="_blank" rel="noreferrer" style={{ color: "#555" }}>{s.url}</a>
              <button onClick={() => handleIngest(s.url)} disabled={loading} title="Fetch new articles from this source">Ingest</button>
            </li>
          ))}
        </ul>
      </div>

      <div>
        <h3>Newsletter</h3>
        <div style={{ display: "flex", gap: "0.5rem", marginBottom: "1rem" }}>
          <button onClick={handleGenerate} disabled={loading}>Generate Draft</button>
          <button onClick={handleSend} disabled={loading || !draft}>Send Email</button>
        </div>
        {draft && (
          <pre style={{ whiteSpace: "pre-wrap", background: "#f6f8fa", padding: "1rem", borderRadius: 8, border: "1px solid #ddd" }}>{draft}</pre>
        )}
      </div>
    </div>
  );
}

export default App;
