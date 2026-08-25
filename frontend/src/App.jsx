import { useState } from "react";
import "./App.css";

const SEVERITY_ORDER = ["Critical", "High", "Medium", "Low"];


function getPriorityClass(priority) {
  if (!priority) return "";

  const value = String(priority).toLowerCase();
  const match = SEVERITY_ORDER.find(
    (level) => level.toLowerCase() === value
  );

  return match ? `priority-${value}` : "";
}

function formatResolution(text) {
  if (!text) return [];

  let cleaned = String(text)
    .replace(/\r/g, "")
    .replace(/\*\*/g, "")
    .replace(/```/g, "")
    .trim();

  let points = cleaned
    .split(/\n+/)
    .map((item) => item.trim())
    .filter(Boolean);

  if (points.length === 1) {
    points = cleaned
      .split(/(?=\d+[\.\)]\s+)/)
      .map((item) => item.trim())
      .filter(Boolean);
  }

  if (points.length === 1) {
    points = cleaned
      .split(/(?<=[.!?])\s+(?=[A-Z])/)
      .map((item) => item.trim())
      .filter(Boolean);
  }

  return points.map((point) =>
    point
      .replace(/^(\d+[\.\)]|[-•*])\s*/, "")
      .trim()
  );
}

const workflowSteps = [
  "Capture the ticket and classify the incident type",
  "Predict the appropriate support queue and priority",
  "Search similar historical cases using semantic retrieval",
  "Generate a grounded resolution recommendation from past evidence",
];

function App() {
  const [ticket, setTicket] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const analyzeTicket = async () => {
    if (!ticket.trim()) {
      setError("Please enter a ticket description.");
      return;
    }

    setLoading(true);
    setError("");
    setResult(null);

    try {
      const rawApiBaseUrl =
        import.meta.env.VITE_API_BASE_URL ||
        "https://ai-enterprise-workflow-incident.onrender.com";
      const apiBaseUrl = rawApiBaseUrl.replace(/\/+$/, "");
      
      const response = await fetch(`${apiBaseUrl}/analyze-ticket`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          ticket: ticket.trim(),
        }),
      });

      if (!response.ok) {
        let errDetails = "";
        try {
          const errJson = await response.json();
          errDetails = errJson.detail || errJson.message || "";
        } catch {
          // Ignore JSON parse errors
        }
        throw new Error(
          errDetails
            ? `Server Error (${response.status}): ${errDetails}`
            : `API request failed with status ${response.status}`
        );
      }

      const data = await response.json();
      setResult(data);
    } catch (err) {
      console.error(err);
      setError(
        err.message ||
        "Couldn't connect to the deployed backend. Please verify the API URL or try again later."
      );
    } finally {
      setLoading(false);
    }
  };

  const priorityClass = getPriorityClass(result?.priority);
  const resolutionText =
    result?.resolution || result?.suggested_resolution || "";
  const resolutionSteps = formatResolution(resolutionText);

  return (
    <div className="app-shell">
      <main className="workspace">
        <header className="topbar">
          <div>
            <p className="eyebrow">AI enterprise workflow</p>
            <h1>Incident Intelligence Platform</h1>
            <p className="subtitle">
              AI-powered ticket triage, queue routing, and resolution guidance for
              enterprise IT support teams.
            </p>
          </div>
        </header>

        <section className="content-grid">
          <div className="panel intake-panel">
            <div className="panel-header">
              <div>
                <span className="eyebrow">AI triage</span>
                <h3>Support ticket intake</h3>
              </div>
              <span className="live-pill">Live</span>
            </div>

            <label htmlFor="ticket">Ticket description</label>
            <textarea
              id="ticket"
              value={ticket}
              onChange={(event) => setTicket(event.target.value)}
              placeholder="Example: Employees cannot access the internal VPN from the London office..."
            />

            <div className="textarea-meta">
              <span>{ticket.length} characters</span>
              <span>Ready for analysis</span>
            </div>

            <button
              className="primary-button"
              onClick={analyzeTicket}
              disabled={loading}
            >
              {loading ? (
                <>
                  <span className="button-spinner" />
                  Analyzing ticket
                </>
              ) : (
                <>
                  Run AI analysis
                  <span className="button-arrow">→</span>
                </>
              )}
            </button>

            {error && (
              <div className="error" role="alert">
                {error}
              </div>
            )}
          </div>

          <div className="panel result-panel">
            {!result && !loading && (
              <div className="empty-state">
                <div className="empty-icon">✦</div>
                <span className="eyebrow">Analysis queue</span>
                <h3>No ticket analyzed yet</h3>
                <p>
                  Submit a ticket to receive automated classification, priority
                  assignment, queue routing, and a recommended resolution plan.
                </p>

                <div className="detail-list">
                  {workflowSteps.map((step, index) => (
                    <div key={index} className="detail-item">
                      <span>{index + 1}</span>
                      <p>{step}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {loading && (
              <div className="empty-state">
                <div className="loading-ring" />
                <span className="eyebrow">Processing</span>
                <h3>Evaluating incident context</h3>
                <p>
                  Classifying the issue, reviewing historical matches, and
                  preparing the recommended next actions.
                </p>
              </div>
            )}

            {result && !loading && (
              <div className="analysis-result">
                <div className="result-header-row">
                  <div>
                    <span className="eyebrow">Analysis result</span>
                    <h3>Ticket intelligence summary</h3>
                  </div>
                  <span className="complete-pill">Complete</span>
                </div>

                <div className="result-stats">
                  <div className="stat-box">
                    <span>Category</span>
                    <strong>{result.category || "N/A"}</strong>
                  </div>
                  <div className="stat-box">
                    <span>Priority</span>
                    <strong>
                      <span className={`priority-pill ${priorityClass}`}>
                        {result.priority || "N/A"}
                      </span>
                    </strong>
                  </div>
                  <div className="stat-box">
                    <span>Queue</span>
                    <strong>{result.queue || "N/A"}</strong>
                  </div>
                </div>

                <div className="resolution-box">
                  <div className="resolution-head">
                    <div className="resolution-icon">✓</div>
                    <div>
                      <span className="eyebrow">Recommended action</span>
                      <h4>Suggested resolution</h4>
                    </div>
                  </div>

                  {resolutionSteps.length > 0 ? (
                    <div className="resolution-list">
                      {resolutionSteps.map((step, index) => (
                        <div className="resolution-item" key={index}>
                          <span className="step-number">{index + 1}</span>
                          <p>{step}</p>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="resolution-empty">
                      No resolution recommendation was returned.
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </section>
      </main>
    </div>
  );
}

export default App;