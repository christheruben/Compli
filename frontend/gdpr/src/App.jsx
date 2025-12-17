import { useState } from "react";
import "./App.css";

export default function App() {
  const [input, setInput] = useState("");
  const [reviewText, setReviewText] = useState("");
  const [gdprResult, setGdprResult] = useState(null);
  const [response, setResponse] = useState("");
  const [loading, setLoading] = useState(false);

  // -------------------------------
  // STEP 1: GDPR CHECK
  // -------------------------------
  const checkGdpr = async () => {
    if (!input.trim()) return;
    setLoading(true);

    try {
      const res = await fetch("http://localhost:8000/process_prompt", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: input }),
      });

      const data = await res.json();
      setGdprResult(data);
      setReviewText(data.masked_text);
    } catch (err) {
      alert("Error contacting GDPR service");
    } finally {
      setLoading(false);
    }
  };

  // -------------------------------
  // STEP 2: SEND TO OPENAI
  // -------------------------------
  const sendToOpenAI = async () => {
    if (!reviewText.trim()) return;
    setLoading(true);

    try {
      const res = await fetch("http://localhost:8000/openai_chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: reviewText }),
      });

      const data = await res.json();
      setResponse(data.response);
    } catch {
      alert("Error contacting OpenAI");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container">
      <h1>GDPR-Compliant Chat</h1>

      {/* INITIAL INPUT */}
      {!gdprResult && (
        <>
          <textarea
            placeholder="Enter your prompt..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
          />

          <div className="button-row">
            <button
              className="btn-primary"
              onClick={checkGdpr}
              disabled={loading}
            >
              {loading ? "Checking..." : "Check GDPR"}
            </button>
          </div>
        </>
      )}

      {/* GDPR REVIEW */}
      {gdprResult && (
        <>
          <h2>Review & Edit Prompt</h2>

          <textarea
            value={reviewText}
            onChange={(e) => setReviewText(e.target.value)}
          />

          {gdprResult.blocked && (
            <div className="gdpr-warning">
              <strong>GDPR Issues Detected</strong>
              <ul>
                {Object.keys(gdprResult.detections?.regex || {}).length > 0 && (
                  <li>PII detected (emails, phone numbers, etc.)</li>
                )}
                {Object.keys(gdprResult.detections?.ner || {}).length > 0 && (
                  <li>Named individuals or locations detected</li>
                )}
                {(gdprResult.detections?.special_categories || []).length > 0 && (
                  <li>
                    Special category data:{" "}
                    {gdprResult.detections.special_categories.join(", ")}
                  </li>
                )}
              </ul>
              <p>Please remove or anonymize this data before submitting.</p>
            </div>
          )}

          <div className="button-row">
            <button
              className="btn-secondary"
              onClick={() => {
                setGdprResult(null);
                setResponse("");
              }}
            >
              Start Over
            </button>

            <button
              className={
                gdprResult.blocked ? "btn-disabled" : "btn-success"
              }
              onClick={sendToOpenAI}
              disabled={gdprResult.blocked || loading}
            >
              Send to OpenAI
            </button>
          </div>
        </>
      )}

      {/* AI RESPONSE */}
      {response && (
        <div className="ai-response">
          <h2>AI Response</h2>
          <div className="ai-response-content">
            {response}
          </div>
        </div>
      )}
    </div>
  );
}
