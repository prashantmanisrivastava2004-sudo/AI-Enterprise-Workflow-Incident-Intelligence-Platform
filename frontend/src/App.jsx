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

/*
  Converts the LLM resolution into clean steps.

  Handles:
  1. Step one
  2. Step two

  - Step one
  - Step two

  Step one. Step two.
*/
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

  // Split numbered items if they were returned on one line
  if (points.length === 1) {
    points = cleaned
      .split(/(?=\d+[\.\)]\s+)/)
      .map((item) => item.trim())
      .filter(Boolean);
  }

  // If still one paragraph, split into sentences
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
      const response = await fetch(
        "http://127.0.0.1:8000/analyze-ticket",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            ticket: ticket.trim(),
          }),
        }
      );

      if (!response.ok) {
        throw new Error(`API request failed: ${response.status}`);
      }

      const data = await response.json();

      setResult(data);
    } catch (err) {
      console.error(err);

      setError(
        "Couldn't connect to the backend. Make sure FastAPI is running on port 8000."
      );
    } finally {
      setLoading(false);
    }
  };

  const priorityClass = getPriorityClass(result?.priority);

  const resolutionText =
    result?.resolution ||
    result?.suggested_resolution ||
    "";

  const resolutionSteps = formatResolution(resolutionText);

  return (
    <div className="app">

      {/* ================= HEADER ================= */}

      <header className="header">

        <div className="brand">

          <div className="brand-icon">
            <svg
              width="24"
              height="24"
              viewBox="0 0 24 24"
              fill="none"
            >
              <path
                d="M12 2L3 7V13C3 18 6.8 21.6 12 22C17.2 21.6 21 18 21 13V7L12 2Z"
                stroke="currentColor"
                strokeWidth="1.7"
                strokeLinejoin="round"
              />

              <path
                d="M8.5 12L11 14.5L15.5 9.5"
                stroke="currentColor"
                strokeWidth="1.7"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </div>

          <div>
            <span className="brand-eyebrow">
              SUPPORT OPERATIONS
            </span>

            <h1>
              AI Incident Intelligence
            </h1>
          </div>

        </div>

       

      </header>


      {/* ================= MAIN ================= */}

      <main className="console">

        {/* ================= INPUT ================= */}

        <section className="panel input-panel">

          <span className="panel-eyebrow">
            NEW TICKET
          </span>

          <h2 className="ticket-heading">
            Analyze a support ticket
          </h2>

          <p className="subtitle">
            Describe the issue and let the AI pipeline classify
            the ticket, assign priority and queue, and generate
            a recommended resolution.
          </p>


          <label htmlFor="ticket">
            Ticket description
          </label>

          <textarea
            id="ticket"
            value={ticket}
            onChange={(event) =>
              setTicket(event.target.value)
            }
            placeholder="Example: My laptop cannot connect to the office Wi-Fi..."
          />


          <button
            className="submit"
            onClick={analyzeTicket}
            disabled={loading}
          >

            {loading ? (
              <>
                <span className="button-spinner"></span>
                Analyzing...
              </>
            ) : (
              <>
                Analyze ticket
                <span className="button-arrow">
                  →
                </span>
              </>
            )}

          </button>


          {error && (
            <div
              className="error"
              role="alert"
            >
              {error}
            </div>
          )}

        </section>


        {/* ================= RESULTS ================= */}

        <section className="panel result-panel">

          {/* EMPTY */}

          {!result && !loading && (

            <div className="empty-state">

              <div className="empty-icon">

                <svg
                  width="30"
                  height="30"
                  viewBox="0 0 24 24"
                  fill="none"
                >
                  <rect
                    x="3"
                    y="4"
                    width="18"
                    height="16"
                    rx="3"
                    stroke="currentColor"
                    strokeWidth="1.6"
                  />

                  <path
                    d="M7 9H17"
                    stroke="currentColor"
                    strokeWidth="1.6"
                    strokeLinecap="round"
                  />

                  <path
                    d="M7 13H14"
                    stroke="currentColor"
                    strokeWidth="1.6"
                    strokeLinecap="round"
                  />
                </svg>

              </div>

              <span className="panel-eyebrow">
                ANALYSIS
              </span>

              <h2>
                No ticket analyzed yet
              </h2>

              <p>
                Submit a ticket to see its category, priority,
                queue, and recommended resolution.
              </p>

            </div>

          )}


          {/* LOADING */}

          {loading && (

            <div className="empty-state">

              <div className="loading-icon">
                <span className="large-spinner"></span>
              </div>

              <span className="panel-eyebrow">
                ANALYSIS
              </span>

              <h2>
                Analyzing ticket...
              </h2>

              <p>
                Running classification and generating
                the recommended resolution.
              </p>

            </div>

          )}


          {/* RESULT */}

          {result && !loading && (

            <div className="analysis">

              {/* RESULT HEADER */}

              <div className="result-header">

                <div>

                  <span className="panel-eyebrow">
                    ANALYSIS RESULT
                  </span>

                  <h2>
                    Ticket analysis
                  </h2>

                </div>


                <div className="complete-badge">
                  <span></span>
                  Analysis complete
                </div>

              </div>


              {/* ================= PREDICTIONS ================= */}

              <div className="prediction-grid">

                <div className="prediction-card">

                  <span>
                    CATEGORY
                  </span>

                  <strong>
                    {result.category || "N/A"}
                  </strong>

                </div>


                <div className="prediction-card">

                  <span>
                    PRIORITY
                  </span>

                  <strong>

                    <span
                      className={`priority-pill ${priorityClass}`}
                    >
                      {result.priority || "N/A"}
                    </span>

                  </strong>

                </div>


                <div className="prediction-card">

                  <span>
                    QUEUE
                  </span>

                  <strong>
                    {result.queue || "N/A"}
                  </strong>

                </div>

              </div>


              {/* ================= RESOLUTION ================= */}

              <div className="resolution-card">

                <div className="resolution-header">

                  <div className="resolution-icon">

                    <svg
                      width="23"
                      height="23"
                      viewBox="0 0 24 24"
                      fill="none"
                    >
                      <path
                        d="M9 11L11 13L15 9"
                        stroke="currentColor"
                        strokeWidth="1.8"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />

                      <path
                        d="M12 3C7.03 3 3 6.58 3 11C3 13.37 4.15 15.49 6 16.91V21L9.5 19.2C10.3 19.4 11.13 19.5 12 19.5C16.97 19.5 21 15.92 21 11C21 6.58 16.97 3 12 3Z"
                        stroke="currentColor"
                        strokeWidth="1.6"
                        strokeLinejoin="round"
                      />
                    </svg>

                  </div>


                  <div>

                    <span className="panel-eyebrow">
                      RECOMMENDED ACTION
                    </span>

                    <h3>
                      Suggested Resolution
                    </h3>

                  </div>

                </div>


                {resolutionSteps.length > 0 ? (

                  <div className="resolution-content">

                    {resolutionSteps.map(
                      (step, index) => (

                        <div
                          className="resolution-step"
                          key={index}
                        >

                          <div className="step-number">
                            {index + 1}
                          </div>

                          <p>
                            {step}
                          </p>

                        </div>

                      )
                    )}

                  </div>

                ) : (

                  <div className="no-resolution">
                    No resolution recommendation was returned.
                  </div>

                )}

              </div>

            </div>

          )}

        </section>

      </main>

    </div>
  );
}

export default App;