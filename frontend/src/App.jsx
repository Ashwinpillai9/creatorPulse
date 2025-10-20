import { useEffect, useMemo, useState } from "react";
import {
  addSource,
  listSources,
  runPipeline,
  sendNewsletter,
} from "./api/api";

const FONT_FAMILY = "'Inter', 'Segoe UI', sans-serif";
const COLORS = {
  background:
    "linear-gradient(135deg, rgba(3,7,18,1) 0%, rgba(15,23,42,1) 45%, rgba(30,41,59,1) 100%)",
  shell: "rgba(10, 15, 28, 0.85)",
  panel: "rgba(15, 24, 43, 0.92)",
  border: "rgba(148, 163, 184, 0.16)",
  textPrimary: "#e2e8f0",
  textMuted: "#94a3b8",
  accent: "#6366f1",
  accentAlt: "#22d3ee",
};

const STATUS_TONES = {
  pending: {
    bg: "rgba(148,163,184,0.14)",
    color: "#cbd5f5",
    border: "rgba(148,163,184,0.32)",
  },
  running: {
    bg: "rgba(59,130,246,0.18)",
    color: "#60a5fa",
    border: "rgba(59,130,246,0.45)",
  },
  completed: {
    bg: "rgba(34,197,94,0.18)",
    color: "#4ade80",
    border: "rgba(34,197,94,0.45)",
  },
  error: {
    bg: "rgba(248,113,113,0.2)",
    color: "#f87171",
    border: "rgba(248,113,113,0.45)",
  },
};

const STEP_FLOW = [
  {
    key: "source",
    label: "Step 1",
    title: "Step 1 - Source Intake",
    subtitle: "Choose which sources to include or add a new feed.",
  },
  {
    key: "fetch",
    label: "Step 2",
    title: "Step 2 - Fetch Data",
    subtitle: "Pull the latest items from your selected feeds.",
  },
  {
    key: "curate",
    label: "Step 3",
    title: "Step 3 - Curate Top 10",
    subtitle: "Review the stories that made the cut for the briefing.",
  },
  {
    key: "summarize",
    label: "Step 4",
    title: "Step 4 - Summaries",
    subtitle: "Ensure each story has a crisp summary with impact.",
  },
  {
    key: "preview",
    label: "Step 5",
    title: "Step 5 - Draft Preview",
    subtitle: "Confirm the HTML newsletter is polished and on-brand.",
  },
  {
    key: "send",
    label: "Step 6",
    title: "Step 6 - Approval & Send",
    subtitle: "Ship the newsletter once everything looks perfect.",
  },
];

const createInitialSteps = () =>
  STEP_FLOW.map((step, index) => ({
    ...step,
    status: index === 0 ? "running" : "pending",
    meta: {},
  }));

const createPendingSteps = () =>
  STEP_FLOW.map((step, index) => ({
    ...step,
    status: index === 0 ? "running" : "pending",
    meta: {},
  }));

const mergeStepUpdates = (steps, updates = []) =>
  steps.map((step) => {
    const update = updates.find((u) => u.stage === step.key);
    if (!update) return step;
    return {
      ...step,
      status: update.status,
      meta: { ...step.meta, ...update },
    };
  });

const resolveTone = (status) => {
  const normalized = (status || "").toLowerCase();
  if (normalized === "running" || normalized === "active") return "running";
  if (
    normalized === "completed" ||
    normalized === "done" ||
    normalized === "added" ||
    normalized === "existing"
  )
    return "completed";
  if (normalized === "error" || normalized === "failed") return "error";
  if (normalized === "skipped") return "pending";
  return "pending";
};

const metaSummary = (step) => {
  if (step.key === "source") {
    if (step.meta?.action === "added") return "Source added";
    if (step.meta?.action === "existing") return "Existing source";
  }
  if (step.key === "fetch" && typeof step.meta?.inserted === "number") {
    return `${step.meta.inserted} new items`;
  }
  if (step.key === "curate" && typeof step.meta?.stories === "number") {
    return `${step.meta.stories} stories`;
  }
  if (step.key === "preview" && step.meta?.hasDraft) {
    return "Draft ready";
  }
  if (step.key === "send" && step.meta?.sent) {
    return "Sent";
  }
  return null;
};

const stepButtonBase = {
  display: "flex",
  flexDirection: "column",
  alignItems: "flex-start",
  gap: "4px",
  minWidth: "120px",
  padding: "12px 18px",
  borderRadius: "16px",
  border: "1px solid transparent",
  background: "transparent",
  fontFamily: FONT_FAMILY,
  fontWeight: 600,
  cursor: "pointer",
  transition: "all 0.2s ease",
};

const panelStyle = {
  background: COLORS.panel,
  border: `1px solid ${COLORS.border}`,
  borderRadius: "28px",
  padding: "32px 36px",
  boxShadow: "0 28px 60px rgba(2, 6, 23, 0.45)",
  backdropFilter: "blur(18px)",
};

function App() {
  const [sources, setSources] = useState([]);
  const [selectedSourceIds, setSelectedSourceIds] = useState([]);
  const [newSourceName, setNewSourceName] = useState("");
  const [newSourceUrl, setNewSourceUrl] = useState("");
  const [ingestExisting, setIngestExisting] = useState(true);

  const [pipelineSteps, setPipelineSteps] = useState(createInitialSteps);
  const [manualStepKey, setManualStepKey] = useState(null);
  const [pipelineLoading, setPipelineLoading] = useState(false);
  const [sendLoading, setSendLoading] = useState(false);
  const [stories, setStories] = useState([]);
  const [draftHtml, setDraftHtml] = useState("");
  const [draftText, setDraftText] = useState("");
  const [error, setError] = useState("");
  const [toast, setToast] = useState("");

  useEffect(() => {
    refreshSources();
  }, []);

  const activeKeyComputed = useMemo(
    () => nextActiveKey(pipelineSteps),
    [pipelineSteps]
  );
  const selectedStepKey = manualStepKey || activeKeyComputed;
  const selectedStep =
    pipelineSteps.find((step) => step.key === selectedStepKey) ||
    pipelineSteps[0];

  async function refreshSources() {
    try {
      const { data } = await listSources();
      const items = data || [];
      setSources(items);
      setSelectedSourceIds((prev) => {
        if (!prev.length) {
          return items.map((item) => item.id);
        }
        const available = items
          .filter((item) => prev.includes(item.id))
          .map((item) => item.id);
        return available.length ? available : items.map((item) => item.id);
      });
    } catch (err) {
      console.error(err);
      setError("Unable to load sources. Check backend connection.");
    }
  }

  const handleAddSource = async () => {
    if (!newSourceName || !newSourceUrl) {
      setError("Please provide both a source name and URL.");
      return;
    }
    setError("");
    try {
      const response = await addSource(newSourceName, newSourceUrl);
      const inserted =
        Array.isArray(response.data) && response.data.length
          ? response.data[0]
          : null;
      if (inserted?.id) {
        setSelectedSourceIds((prev) =>
          Array.from(new Set([...prev, inserted.id]))
        );
      }
      setToast("Source added. It will be part of the next pipeline run.");
      setNewSourceName("");
      setNewSourceUrl("");
      await refreshSources();
      setManualStepKey("source");
    } catch (err) {
      console.error(err);
      const message =
        err.response?.data?.detail || "Failed to add source. Please try again.";
      setError(message);
    }
  };

  const toggleSourceSelection = (id) => {
    setSelectedSourceIds((prev) => {
      if (prev.includes(id)) {
        return prev.filter((value) => value !== id);
      }
      return [...prev, id];
    });
  };

  const handleSelectAll = () => {
    setSelectedSourceIds(sources.map((source) => source.id));
  };

  const handleClearSelection = () => {
    setSelectedSourceIds([]);
  };

  const handleRunPipeline = async () => {
    setManualStepKey(null);
    setError("");
    setToast("");

    if (!selectedSourceIds.length && !newSourceUrl) {
      setError("Select at least one source or add a new feed before running.");
      return;
    }

    setPipelineLoading(true);
    setDraftHtml("");
    setDraftText("");
    setStories([]);
    setPipelineSteps(createPendingSteps());

    const payload = {
      ingest_existing: ingestExisting,
      source_ids: selectedSourceIds,
    };
    if (newSourceUrl) {
      payload.source_url = newSourceUrl;
      if (newSourceName) {
        payload.source_name = newSourceName;
      }
    }

    try {
      const res = await runPipeline(payload);
      const updates = res.data.steps || [];
      let updated = mergeStepUpdates(createPendingSteps(), updates);

      updated = updated.map((step) => {
        if (step.key === "send") {
          return { ...step, status: "pending" };
        }
        return step;
      });

      setPipelineSteps(updated);
      setDraftHtml(res.data.html || "");
      setDraftText(res.data.text || "");
      setStories(res.data.stories || []);
      if (Array.isArray(res.data.used_source_ids)) {
        setSelectedSourceIds(res.data.used_source_ids);
      }
      setToast("Pipeline complete. Review the draft before sending.");
      if (!newSourceUrl) {
        await refreshSources();
      }
      setManualStepKey("preview");
    } catch (err) {
      console.error(err);
      const message =
        err.response?.data?.error ||
        err.response?.data?.detail ||
        err.message ||
        "Pipeline failed. Please try again.";
      const errorSteps = err.response?.data?.steps;
      if (errorSteps) {
        setPipelineSteps(mergeStepUpdates(createPendingSteps(), errorSteps));
      } else {
        setPipelineSteps((prev) =>
          prev.map((step, index) =>
            index === 0 ? { ...step, status: "error" } : { ...step, status: "pending" }
          )
        );
      }
      setError(message);
      setManualStepKey("source");
    } finally {
      setPipelineLoading(false);
    }
  };

  const handleSend = async () => {
    setError("");
    setToast("");
    setSendLoading(true);
    try {
      await sendNewsletter({ source_ids: selectedSourceIds });
      setPipelineSteps((prev) =>
        prev.map((step) =>
          step.key === "send"
            ? { ...step, status: "completed", meta: { ...step.meta, sent: true } }
            : step
        )
      );
      setToast("Newsletter sent successfully.");
    } catch (err) {
      console.error(err);
      setError("Failed to send newsletter. Try again later.");
      setPipelineSteps((prev) =>
        prev.map((step) =>
          step.key === "send"
            ? { ...step, status: "error", meta: { ...step.meta, sent: false } }
            : step
        )
      );
    } finally {
      setSendLoading(false);
    }
  };

  const renderSourceList = () => {
    if (!sources.length) {
      return (
        <div
          style={{
            border: `1px dashed ${COLORS.border}`,
            borderRadius: "16px",
            padding: "18px",
            textAlign: "center",
            color: COLORS.textMuted,
            fontFamily: FONT_FAMILY,
          }}
        >
          Add your first feed to start building the briefing.
        </div>
      );
    }

    return (
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          gap: "12px",
        }}
      >
        {sources.map((source) => {
          const checked = selectedSourceIds.includes(source.id);
          return (
            <label
              key={source.id}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "14px",
                padding: "14px 18px",
                borderRadius: "16px",
                border: `1px solid ${checked ? COLORS.accent : COLORS.border}`,
                background: checked
                  ? "rgba(99,102,241,0.14)"
                  : "rgba(255,255,255,0.02)",
                boxShadow: checked
                  ? "0 12px 30px rgba(99,102,241,0.18)"
                  : "0 6px 18px rgba(8,12,24,0.32)",
                transition: "all 0.2s ease",
                cursor: "pointer",
              }}
            >
              <input
                type="checkbox"
                checked={checked}
                onChange={() => toggleSourceSelection(source.id)}
                style={{ width: 18, height: 18, accentColor: COLORS.accent }}
              />
              <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                <span style={{ color: COLORS.textPrimary, fontWeight: 600 }}>
                  {source.name}
                </span>
                <span style={{ color: COLORS.textMuted, fontSize: "0.9rem" }}>
                  {source.url}
                </span>
              </div>
            </label>
          );
        })}
      </div>
    );
  };

  const renderStoriesList = (showSummary = false) => {
    if (!stories.length) {
      return (
        <div
          style={{
            border: `1px dashed ${COLORS.border}`,
            borderRadius: "16px",
            padding: "18px",
            textAlign: "center",
            color: COLORS.textMuted,
          }}
        >
          Run the pipeline to curate today's stories.
        </div>
      );
    }

    return (
      <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
        {stories.map((story, index) => (
          <div
            key={story.url ?? index}
            style={{
              border: `1px solid ${COLORS.border}`,
              borderRadius: "18px",
              padding: "18px 20px",
              background: "rgba(255,255,255,0.02)",
              boxShadow: "0 8px 24px rgba(8,12,24,0.35)",
              display: "flex",
              flexDirection: "column",
              gap: "8px",
            }}
          >
            <span
              style={{
                fontSize: "0.8rem",
                letterSpacing: "0.18em",
                textTransform: "uppercase",
                color: COLORS.textMuted,
              }}
            >
              Story {index + 1}
            </span>
            <h3 style={{ margin: 0, color: COLORS.textPrimary, fontSize: "1.05rem" }}>
              {story.title}
            </h3>
            {showSummary && (
              <p style={{ margin: 0, color: COLORS.textMuted, fontSize: "0.95rem" }}>
                {story.summary}
              </p>
            )}
            {story.url && (
              <a
                href={story.url}
                target="_blank"
                rel="noreferrer"
                style={{ color: COLORS.accent, fontSize: "0.9rem" }}
              >
                View original article
              </a>
            )}
          </div>
        ))}
      </div>
    );
  };

  const renderPreview = () => {
    if (!draftHtml) {
      return (
        <div
          style={{
            border: `1px dashed ${COLORS.border}`,
            borderRadius: "18px",
            padding: "20px",
            textAlign: "center",
            color: COLORS.textMuted,
          }}
        >
          Generate a draft to see the preview.
        </div>
      );
    }
    return (
      <div
        style={{
          border: `1px solid ${COLORS.border}`,
          borderRadius: "20px",
          background: "rgba(255,255,255,0.03)",
          boxShadow: "0 24px 60px rgba(8,12,24,0.45)",
          maxHeight: "520px",
          overflow: "auto",
        }}
        dangerouslySetInnerHTML={{ __html: draftHtml }}
      />
    );
  };

  const renderStepContent = () => {
    switch (selectedStepKey) {
      case "source":
        return (
          <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
            <div
              style={{
                display: "flex",
                flexWrap: "wrap",
                gap: "12px",
              }}
            >
              <input
                type="text"
                value={newSourceName}
                onChange={(e) => setNewSourceName(e.target.value)}
                placeholder="Source name"
                style={{
                  flex: "1 1 220px",
                  padding: "12px 16px",
                  borderRadius: "14px",
                  border: `1px solid ${COLORS.border}`,
                  background: "rgba(12,18,30,0.8)",
                  color: COLORS.textPrimary,
                  fontFamily: FONT_FAMILY,
                }}
              />
              <input
                type="url"
                value={newSourceUrl}
                onChange={(e) => setNewSourceUrl(e.target.value)}
                placeholder="Feed URL"
                style={{
                  flex: "2 1 280px",
                  padding: "12px 16px",
                  borderRadius: "14px",
                  border: `1px solid ${COLORS.border}`,
                  background: "rgba(12,18,30,0.8)",
                  color: COLORS.textPrimary,
                  fontFamily: FONT_FAMILY,
                }}
              />
              <button
                type="button"
                onClick={handleAddSource}
                style={{
                  padding: "12px 18px",
                  borderRadius: "14px",
                  border: "none",
                  background: `linear-gradient(135deg, ${COLORS.accent}, ${COLORS.accentAlt})`,
                  color: "#0f172a",
                  fontWeight: 600,
                  cursor: "pointer",
                  transition: "transform 0.2s ease",
                }}
              >
                Add
              </button>
            </div>

            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                flexWrap: "wrap",
                gap: "12px",
                color: COLORS.textMuted,
              }}
            >
              <span>
                {selectedSourceIds.length}/{sources.length} sources selected
              </span>
              <div style={{ display: "flex", gap: "10px" }}>
                <button
                  type="button"
                  onClick={handleSelectAll}
                  style={{
                    padding: "8px 14px",
                    borderRadius: "12px",
                    border: `1px solid ${COLORS.border}`,
                    background: "rgba(255,255,255,0.04)",
                    color: COLORS.textPrimary,
                    cursor: "pointer",
                  }}
                >
                  Select all
                </button>
                <button
                  type="button"
                  onClick={handleClearSelection}
                  style={{
                    padding: "8px 14px",
                    borderRadius: "12px",
                    border: `1px solid ${COLORS.border}`,
                    background: "rgba(255,255,255,0.04)",
                    color: COLORS.textPrimary,
                    cursor: "pointer",
                  }}
                >
                  Clear
                </button>
              </div>
            </div>

            <label
              style={{
                display: "flex",
                alignItems: "center",
                gap: "8px",
                color: COLORS.textMuted,
              }}
            >
              <input
                type="checkbox"
                checked={ingestExisting}
                onChange={(e) => setIngestExisting(e.target.checked)}
              />
              Re-ingest all selected sources before curating the briefing
            </label>

            <button
              type="button"
              onClick={handleRunPipeline}
              disabled={pipelineLoading}
              style={{
                alignSelf: "flex-start",
                padding: "12px 24px",
                borderRadius: "16px",
                border: "none",
                background: pipelineLoading
                  ? "rgba(99,102,241,0.35)"
                  : `linear-gradient(135deg, ${COLORS.accent}, ${COLORS.accentAlt})`,
                color: "#0f172a",
                fontWeight: 700,
                cursor: pipelineLoading ? "not-allowed" : "pointer",
                boxShadow: pipelineLoading
                  ? "none"
                  : "0 18px 40px rgba(99,102,241,0.28)",
                transition: "all 0.2s ease",
              }}
            >
              {pipelineLoading ? "Running pipeline..." : "Run Pipeline"}
            </button>

            {renderSourceList()}
          </div>
        );
      case "fetch": {
        const meta = selectedStep.meta || {};
        return (
          <div style={{ color: COLORS.textMuted, display: "flex", flexDirection: "column", gap: "16px" }}>
            <p style={{ margin: 0 }}>
              Fetch pulls the freshest entries from each selected feed. The last run added{" "}
              <strong style={{ color: COLORS.textPrimary }}>
                {meta.inserted ?? 0}
              </strong>{" "}
              new items.
            </p>
            <p style={{ margin: 0 }}>
              Tweak the re-ingestion toggle in Step 1 if you want to skip pulling updates.
            </p>
          </div>
        );
      }
      case "curate":
        return (
          <div style={{ display: "flex", flexDirection: "column", gap: "18px" }}>
            <p style={{ margin: 0, color: COLORS.textMuted }}>
              These are the ten stories that will headline the briefing.
            </p>
            {renderStoriesList(false)}
          </div>
        );
      case "summarize":
        return (
          <div style={{ display: "flex", flexDirection: "column", gap: "18px" }}>
            <p style={{ margin: 0, color: COLORS.textMuted }}>
              Each summary ends with a “Why it matters” insight to highlight impact.
            </p>
            {renderStoriesList(true)}
          </div>
        );
      case "preview":
        return (
          <div style={{ display: "flex", flexDirection: "column", gap: "18px" }}>
            <p style={{ margin: 0, color: COLORS.textMuted }}>
              Review the HTML email exactly as subscribers will see it.
            </p>
            {renderPreview()}
          </div>
        );
      case "send":
      default:
        return (
          <div style={{ display: "flex", flexDirection: "column", gap: "18px" }}>
            <p style={{ margin: 0, color: COLORS.textMuted }}>
              Ready to go? Approve the draft to send it to your list.
            </p>
            <button
              type="button"
              onClick={handleSend}
              disabled={!draftHtml || sendLoading}
              style={{
                alignSelf: "flex-start",
                padding: "12px 24px",
                borderRadius: "16px",
                border: "none",
                background:
                  !draftHtml || sendLoading
                    ? "rgba(99,102,241,0.25)"
                    : `linear-gradient(135deg, ${COLORS.accent}, ${COLORS.accentAlt})`,
                color: "#0f172a",
                fontWeight: 700,
                cursor: !draftHtml || sendLoading ? "not-allowed" : "pointer",
                boxShadow:
                  !draftHtml || sendLoading
                    ? "none"
                    : "0 18px 40px rgba(99,102,241,0.28)",
              }}
            >
              {sendLoading ? "Sending..." : "Approve & Send"}
            </button>
            <p style={{ margin: 0, color: COLORS.textMuted }}>
              Tip: rerun the pipeline if you want to refresh the lineup before sending.
            </p>
          </div>
        );
    }
  };

  const heroShellStyle = {
    background: COLORS.shell,
    borderRadius: "36px",
    border: `1px solid ${COLORS.border}`,
    padding: "40px 48px",
    boxShadow: "0 40px 90px rgba(2, 6, 23, 0.55)",
    backdropFilter: "blur(20px)",
    width: "100%",
    maxWidth: "1040px",
    display: "flex",
    flexDirection: "column",
    gap: "28px",
  };

  const allSelected =
    sources.length > 0 && selectedSourceIds.length === sources.length;

  return (
    <div
      style={{
        minHeight: "100vh",
        background: COLORS.background,
        padding: "48px 24px",
        display: "flex",
        justifyContent: "center",
        fontFamily: FONT_FAMILY,
        color: COLORS.textPrimary,
      }}
    >
      <div style={heroShellStyle}>
        <header
          style={{
            textAlign: "center",
            display: "flex",
            flexDirection: "column",
            gap: "10px",
          }}
        >
          <span
            style={{
              fontSize: "0.8rem",
              letterSpacing: "0.4em",
              textTransform: "uppercase",
              color: COLORS.textMuted,
            }}
          >
            Creator Pulse
          </span>
          <h1 style={{ margin: 0, fontSize: "2.4rem" }}>
            Funky newsroom workflow, streamlined.
          </h1>
          <p style={{ margin: 0, color: COLORS.textMuted }}>
            Follow the six-step pipeline to select sources, curate the top ten stories,
            polish the draft, and ship the newsletter with confidence.
          </p>
        </header>

        <nav
          style={{
            display: "flex",
            flexWrap: "wrap",
            gap: "16px",
            justifyContent: "center",
          }}
        >
          {pipelineSteps.map((step) => {
            const toneKey = resolveTone(step.status);
            const tone = STATUS_TONES[toneKey] || STATUS_TONES.pending;
            const isActive = step.key === selectedStepKey;
            const meta = metaSummary(step);
            return (
              <button
                key={step.key}
                type="button"
                style={{
                  ...stepButtonBase,
                  background: isActive
                    ? `linear-gradient(135deg, ${COLORS.accent}, ${COLORS.accentAlt})`
                    : tone.bg,
                  color: isActive ? "#0f172a" : tone.color,
                  border: `1px solid ${isActive ? COLORS.accent : tone.border}`,
                  boxShadow: isActive
                    ? "0 16px 34px rgba(99,102,241,0.35)"
                    : "0 12px 30px rgba(8,12,24,0.45)",
                  transform: isActive ? "translateY(-3px)" : "translateY(0)",
                }}
                onClick={() => setManualStepKey(step.key)}
              >
                <span>{step.label}</span>
                <small style={{ fontWeight: 500, opacity: 0.92 }}>
                  {toneKey === "completed"
                    ? "Done"
                    : toneKey === "running"
                    ? "In progress"
                    : toneKey === "error"
                    ? "Needs attention"
                    : allSelected && step.key === "source"
                    ? "All sources"
                    : "Pending"}
                </small>
                {meta && (
                  <span style={{ fontSize: "0.75rem", opacity: 0.9 }}>{meta}</span>
                )}
              </button>
            );
          })}
        </nav>

        {(error || toast) && (
          <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            {error && (
              <div
                style={{
                  background: "rgba(248,113,113,0.15)",
                  border: "1px solid rgba(248,113,113,0.4)",
                  borderRadius: "18px",
                  padding: "14px 18px",
                  color: "#fca5a5",
                }}
              >
                {error}
              </div>
            )}
            {toast && (
              <div
                style={{
                  background: "rgba(34,197,94,0.18)",
                  border: "1px solid rgba(34,197,94,0.4)",
                  borderRadius: "18px",
                  padding: "14px 18px",
                  color: "#86efac",
                }}
              >
                {toast}
              </div>
            )}
          </div>
        )}

        <section style={panelStyle}>
          <header style={{ marginBottom: "18px" }}>
            <h2 style={{ margin: 0, fontSize: "1.6rem" }}>{selectedStep.title}</h2>
            <p style={{ margin: 0, color: COLORS.textMuted }}>{selectedStep.subtitle}</p>
          </header>
          {renderStepContent()}
        </section>
      </div>
    </div>
  );
}

function nextActiveKey(steps) {
  const pendingStep = steps.find(
    (step) =>
      !["completed", "skipped"].includes((step.status || "").toLowerCase())
  );
  return pendingStep ? pendingStep.key : steps[steps.length - 1].key;
}

export default App;
