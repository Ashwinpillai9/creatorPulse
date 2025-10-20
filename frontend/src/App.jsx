import { useEffect, useMemo, useState } from "react";
import {
  addSource,
  listSources,
  runPipeline,
  sendNewsletter,
} from "./api/api";

const STEP_FLOW = [
  {
    key: "source",
    label: "Step 1",
    title: "Step 1 - Source Intake",
    subtitle: "Add an optional data source or pick an existing one to include.",
  },
  {
    key: "fetch",
    label: "Step 2",
    title: "Step 2 - Fetch Data",
    subtitle: "Pull the latest items from your configured feeds.",
  },
  {
    key: "curate",
    label: "Step 3",
    title: "Step 3 - Curate Top 10",
    subtitle: "Review the stories selected for today's briefing.",
  },
  {
    key: "summarize",
    label: "Step 4",
    title: "Step 4 - Summaries",
    subtitle: "Check that every story has a clean newsroom-style summary.",
  },
  {
    key: "preview",
    label: "Step 5",
    title: "Step 5 - Draft Preview",
    subtitle: "Confirm the HTML newsletter looks ready to ship.",
  },
  {
    key: "send",
    label: "Step 6",
    title: "Step 6 - Approval & Send",
    subtitle: "Send the newsletter once everything is in place.",
  },
];

const FONT_FAMILY = "'Comic Sans MS', 'Patrick Hand', 'Caveat', sans-serif";
const BORDER_COLOR = "#1f2937";
const SKY_BLUE = "#d4e4ff";

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
    if (!update) {
      return step;
    }
    return {
      ...step,
      status: update.status,
      meta: update,
    };
  });

const nextActiveKey = (steps) => {
  const next = steps.find(
    (step) => !["completed", "skipped"].includes(step.status)
  );
  return next ? next.key : STEP_FLOW[STEP_FLOW.length - 1].key;
};

const stepStatusBadge = (status) => {
  switch (status) {
    case "completed":
      return { text: "Done", color: "#10b981" };
    case "running":
    case "active":
      return { text: "In progress", color: "#2563eb" };
    case "pending":
      return { text: "Pending", color: "#64748b" };
    case "skipped":
      return { text: "Skipped", color: "#94a3b8" };
    case "added":
      return { text: "Added", color: "#0ea5e9" };
    case "existing":
      return { text: "Existing", color: "#94a3b8" };
    default:
      return { text: status || "Pending", color: "#64748b" };
  }
};

const sketchFrame = {
  border: `2px solid ${BORDER_COLOR}`,
  borderRadius: "32px",
  background: "#fdfdf8",
  boxShadow: "6px 6px 0 #cbd5f5",
};

const sketchPanel = {
  ...sketchFrame,
  padding: "32px 36px",
};

const sketchButton = (active, completed) => ({
  border: `2px solid ${BORDER_COLOR}`,
  borderRadius: "18px",
  padding: "10px 18px",
  background: active ? SKY_BLUE : "#fffef9",
  color: "#111827",
  fontFamily: FONT_FAMILY,
  fontSize: "0.95rem",
  cursor: "pointer",
  boxShadow: active
    ? "3px 3px 0 #9ca3af"
    : completed
    ? "3px 3px 0 #b2d4ff"
    : "3px 3px 0 #d1d5db",
  outline: "none",
  transition: "transform 0.12s ease",
});

function App() {
  const [sources, setSources] = useState([]);
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

  const fetchStepMeta = (key) =>
    pipelineSteps.find((step) => step.key === key)?.meta || {};

  async function refreshSources() {
    try {
      const res = await listSources();
      setSources(res.data || []);
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
      await addSource(newSourceName, newSourceUrl);
      setToast("Source added. It will be part of the next pipeline run.");
      setNewSourceName("");
      setNewSourceUrl("");
      await refreshSources();
    } catch (err) {
      console.error(err);
      const message =
        err.response?.data?.detail || "Failed to add source. Please try again.";
      setError(message);
    }
  };

  const handleRunPipeline = async () => {
    setManualStepKey(null);
    setError("");
    setToast("");
    setPipelineLoading(true);
    setDraftHtml("");
    setDraftText("");
    setStories([]);

    const payload = {
      ingest_existing: ingestExisting,
    };
    if (newSourceUrl) {
      payload.source_url = newSourceUrl;
      if (newSourceName) {
        payload.source_name = newSourceName;
      }
    }

    setPipelineSteps(createPendingSteps());

    try {
      const res = await runPipeline(payload);
      const updates = res.data.steps || [];
      let updated = mergeStepUpdates(createPendingSteps(), updates);

      updated = updated.map((step) => {
        if (step.key === "preview") {
          return {
            ...step,
            status: res.data.html ? "completed" : step.status,
            meta: { ...step.meta, hasDraft: !!res.data.html },
          };
        }
        if (step.key === "send") {
          return { ...step, status: "pending" };
        }
        return step;
      });

      setPipelineSteps(updated);
      setDraftHtml(res.data.html || "");
      setDraftText(res.data.text || "");
      setStories(res.data.stories || []);
      setToast("Pipeline complete. Review the draft before sending.");
      if (!newSourceUrl) {
        await refreshSources();
      }
    } catch (err) {
      console.error(err);
      const message =
        err.response?.data?.detail || "Pipeline failed. Please try again.";
      setError(message);
      setPipelineSteps(createInitialSteps());
    } finally {
      setPipelineLoading(false);
    }
  };

  const handleSend = async () => {
    setError("");
    setToast("");
    setSendLoading(true);
    try {
      await sendNewsletter();
      setSendLoading(false);
      setToast("Newsletter sent successfully!");
      setPipelineSteps((prev) =>
        prev.map((step) =>
          step.key === "send"
            ? { ...step, status: "completed", meta: { ...step.meta, sent: true } }
            : step
        )
      );
    } catch (err) {
      console.error(err);
      setError("Failed to send newsletter. Try again later.");
      setSendLoading(false);
    }
  };

  const renderSourceList = () => {
    if (sources.length === 0) {
      return (
        <div
          style={{
            border: `2px dashed ${BORDER_COLOR}`,
            borderRadius: "20px",
            padding: "18px",
            textAlign: "center",
            fontFamily: FONT_FAMILY,
            color: "#6b7280",
          }}
        >
          Add a feed to get started.
        </div>
      );
    }

    return (
      <ul
        style={{
          listStyle: "none",
          margin: 0,
          padding: 0,
          display: "flex",
          flexDirection: "column",
          gap: "12px",
        }}
      >
        {sources.map((source) => (
          <li
            key={source.id}
            style={{
              border: `2px solid ${BORDER_COLOR}`,
              borderRadius: "18px",
              padding: "12px 16px",
              background: "#fff",
              display: "flex",
              alignItems: "center",
              gap: "16px",
              fontFamily: FONT_FAMILY,
              boxShadow: "2px 2px 0 #d1d5db",
            }}
          >
            <span
              style={{
                width: "18px",
                height: "18px",
                borderRadius: "50%",
                border: `2px solid ${BORDER_COLOR}`,
                background: "#e0f2fe",
              }}
            />
            <span style={{ flex: 1, fontSize: "0.95rem" }}>{source.name}</span>
            <a
              href={source.url}
              target="_blank"
              rel="noreferrer"
              style={{ color: "#2563eb", fontSize: "0.9rem" }}
            >
              URL
            </a>
          </li>
        ))}
      </ul>
    );
  };

  const renderStoriesList = (withSummary = false) => {
    if (!stories.length) {
      return (
        <div
          style={{
            border: `2px dashed ${BORDER_COLOR}`,
            borderRadius: "20px",
            padding: "18px",
            textAlign: "center",
            fontFamily: FONT_FAMILY,
            color: "#6b7280",
          }}
        >
          Run the pipeline to curate today's stories.
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
        {stories.map((story, idx) => (
          <div
            key={story.url ?? idx}
            style={{
              border: `2px solid ${BORDER_COLOR}`,
              borderRadius: "18px",
              padding: "14px 18px",
              background: "#fff",
              boxShadow: "2px 2px 0 #d1d5db",
              fontFamily: FONT_FAMILY,
              display: "flex",
              flexDirection: "column",
              gap: "6px",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <span
                style={{
                  width: "16px",
                  height: "16px",
                  borderRadius: "50%",
                  border: `2px solid ${BORDER_COLOR}`,
                  background: "#e0f2fe",
                }}
              />
              <span style={{ fontWeight: 600 }}>
                {idx + 1}. {story.title}
              </span>
            </div>
            {withSummary && (
              <p style={{ margin: 0, color: "#4b5563", fontSize: "0.95rem" }}>
                {story.summary}
              </p>
            )}
            {story.url && (
              <a
                href={story.url}
                target="_blank"
                rel="noreferrer"
                style={{ color: "#2563eb", fontSize: "0.9rem" }}
              >
                Read original story
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
            border: `2px dashed ${BORDER_COLOR}`,
            borderRadius: "20px",
            padding: "20px",
            textAlign: "center",
            fontFamily: FONT_FAMILY,
            color: "#6b7280",
          }}
        >
          Generate a draft to see the preview.
        </div>
      );
    }
    return (
      <div
        style={{
          border: `2px solid ${BORDER_COLOR}`,
          borderRadius: "20px",
          background: "#fff",
          boxShadow: "4px 4px 0 #cbd5f5",
          maxHeight: "540px",
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
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              gap: "16px",
              fontFamily: FONT_FAMILY,
            }}
          >
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
                placeholder="Input data source name"
                style={{
                  flex: "1 1 220px",
                  padding: "10px 14px",
                  borderRadius: "14px",
                  border: `2px solid ${BORDER_COLOR}`,
                  boxShadow: "2px 2px 0 #d1d5db",
                  fontFamily: FONT_FAMILY,
                }}
              />
              <input
                type="url"
                value={newSourceUrl}
                onChange={(e) => setNewSourceUrl(e.target.value)}
                placeholder="Input URL"
                style={{
                  flex: "2 1 260px",
                  padding: "10px 14px",
                  borderRadius: "14px",
                  border: `2px solid ${BORDER_COLOR}`,
                  boxShadow: "2px 2px 0 #d1d5db",
                  fontFamily: FONT_FAMILY,
                }}
              />
              <button
                onClick={handleAddSource}
                style={{
                  padding: "10px 18px",
                  borderRadius: "14px",
                  border: `2px solid ${BORDER_COLOR}`,
                  background: SKY_BLUE,
                  boxShadow: "2px 2px 0 #9ca3af",
                  fontFamily: FONT_FAMILY,
                  cursor: "pointer",
                }}
              >
                Add
              </button>
            </div>
            <label
              style={{
                display: "flex",
                alignItems: "center",
                gap: "8px",
                fontSize: "0.95rem",
              }}
            >
              <input
                type="checkbox"
                checked={ingestExisting}
                onChange={(e) => setIngestExisting(e.target.checked)}
              />
              Re-ingest existing sources on the next run
            </label>
            <button
              onClick={handleRunPipeline}
              disabled={pipelineLoading}
              style={{
                alignSelf: "flex-start",
                padding: "10px 22px",
                borderRadius: "18px",
                border: `2px solid ${BORDER_COLOR}`,
                background: pipelineLoading ? "#e5e7eb" : SKY_BLUE,
                boxShadow: "2px 2px 0 #9ca3af",
                fontFamily: FONT_FAMILY,
                cursor: pipelineLoading ? "not-allowed" : "pointer",
                opacity: pipelineLoading ? 0.6 : 1,
              }}
            >
              {pipelineLoading ? "Pipeline running..." : "Run Pipeline"}
            </button>
            {renderSourceList()}
          </div>
        );
      case "fetch": {
        const meta = fetchStepMeta("fetch");
        return (
          <div
            style={{
              fontFamily: FONT_FAMILY,
              display: "flex",
              flexDirection: "column",
              gap: "16px",
            }}
          >
            <p style={{ margin: 0 }}>
              Fetch gathers fresh stories from every source. Last run added{" "}
              <strong>{meta.inserted ?? 0}</strong> new items.
            </p>
            <p style={{ margin: 0, color: "#6b7280" }}>
              Adjust re-ingest settings in Step 1 before running the pipeline.
            </p>
          </div>
        );
      }
      case "curate":
        return (
          <div
            style={{ display: "flex", flexDirection: "column", gap: "16px" }}
          >
            <p style={{ margin: 0, fontFamily: FONT_FAMILY }}>
              These are the ten stories selected for the briefing.
            </p>
            {renderStoriesList(false)}
          </div>
        );
      case "summarize":
        return (
          <div
            style={{ display: "flex", flexDirection: "column", gap: "16px" }}
          >
            <p style={{ margin: 0, fontFamily: FONT_FAMILY }}>
              Each summary ends with a Why it matters insight.
            </p>
            {renderStoriesList(true)}
          </div>
        );
      case "preview":
        return (
          <div
            style={{ display: "flex", flexDirection: "column", gap: "16px" }}
          >
            <p style={{ margin: 0, fontFamily: FONT_FAMILY }}>
              Review the HTML email exactly as subscribers will see it.
            </p>
            {renderPreview()}
          </div>
        );
      case "send":
      default:
        return (
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              gap: "16px",
              fontFamily: FONT_FAMILY,
            }}
          >
            <p style={{ margin: 0 }}>
              When you approve the draft, we will email the newsletter to the configured list.
            </p>
            <button
              onClick={handleSend}
              disabled={!draftHtml || sendLoading}
              style={{
                alignSelf: "flex-start",
                padding: "10px 22px",
                borderRadius: "18px",
                border: `2px solid ${BORDER_COLOR}`,
                background: !draftHtml || sendLoading ? "#e5e7eb" : SKY_BLUE,
                boxShadow: "2px 2px 0 #9ca3af",
                fontFamily: FONT_FAMILY,
                cursor: !draftHtml || sendLoading ? "not-allowed" : "pointer",
                opacity: !draftHtml || sendLoading ? 0.6 : 1,
              }}
            >
              {sendLoading ? "Sending..." : "Approve & Send"}
            </button>
            <p style={{ margin: 0, color: "#6b7280" }}>
              Tip: run the pipeline again if you want a fresh draft before sending.
            </p>
          </div>
        );
    }
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "#f5f5f2",
        padding: "36px 20px",
        fontFamily: FONT_FAMILY,
        color: "#111827",
        display: "flex",
        justifyContent: "center",
      }}
    >
      <div
        style={{
          ...sketchFrame,
          width: "100%",
          maxWidth: "960px",
          padding: "32px 40px",
          display: "flex",
          flexDirection: "column",
          gap: "24px",
        }}
      >
        <header
          style={{
            textAlign: "center",
            display: "flex",
            flexDirection: "column",
            gap: "8px",
          }}
        >
          <h1 style={{ margin: 0, fontSize: "2rem" }}>Creator Pulse</h1>
          <p style={{ margin: 0, color: "#475569" }}>
            Follow the steps to craft and approve today's newsletter.
          </p>
        </header>

        <nav
          style={{
            display: "flex",
            flexWrap: "wrap",
            gap: "12px",
            justifyContent: "center",
          }}
        >
          {pipelineSteps.map((step) => {
            const badge = stepStatusBadge(step.status);
            const isCompleted = step.status === "completed";
            const isActive = step.key === selectedStepKey;
            return (
              <button
                key={step.key}
                type="button"
                style={sketchButton(isActive, isCompleted)}
                onClick={() => setManualStepKey(step.key)}
              >
                <div style={{ fontWeight: 600 }}>{step.label}</div>
                <div style={{ fontSize: "0.75rem", color: badge.color }}>
                  {badge.text}
                </div>
              </button>
            );
          })}
        </nav>

        {(error || toast) && (
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              gap: "12px",
            }}
          >
            {error && (
              <div
                style={{
                  ...sketchFrame,
                  borderColor: "#dc2626",
                  boxShadow: "4px 4px 0 #fecaca",
                  padding: "12px 16px",
                }}
              >
                {error}
              </div>
            )}
            {toast && (
              <div
                style={{
                  ...sketchFrame,
                  borderColor: "#16a34a",
                  boxShadow: "4px 4px 0 #bbf7d0",
                  padding: "12px 16px",
                }}
              >
                {toast}
              </div>
            )}
          </div>
        )}

        <section style={sketchPanel}>
          <header
            style={{
              display: "flex",
              flexDirection: "column",
              gap: "4px",
              marginBottom: "18px",
            }}
          >
            <h2 style={{ margin: 0, fontSize: "1.4rem" }}>{selectedStep.title}</h2>
            <p style={{ margin: 0, color: "#475569" }}>{selectedStep.subtitle}</p>
          </header>
          {renderStepContent()}
        </section>
      </div>
    </div>
  );
}

export default App;
