
import { useState } from "react";
import axios from "axios";

export default function QuestionForm({ onSubmitted, user }) {
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [validationError, setValidationError] = useState("");
  const api = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

  const validateWithXHR = (text) => {
    return new Promise((resolve) => {
      const xhr = new XMLHttpRequest();
      const url = `${api}/validate`;
      xhr.open("POST", url, true);
      xhr.setRequestHeader("Content-Type", "application/json;charset=UTF-8");

      xhr.onreadystatechange = () => {
        if (xhr.readyState !== 4) return;
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            const res = JSON.parse(xhr.responseText);
            resolve(res);
          } catch (e) {
            resolve({ valid: false, reason: "Invalid server response." });
          }
        } else {
          resolve({ valid: false, reason: "Validation service unavailable." });
        }
      };

      try {
        xhr.send(JSON.stringify({ message: text }));
      } catch (e) {
        resolve({ valid: false, reason: "Failed to run validation." });
      }

      setTimeout(() => resolve({ valid: false, reason: "Validation timed out." }), 3000);
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setValidationError("");
    if (!message || !message.trim()) {
      setValidationError("Question cannot be blank.");
      return;
    }

    setLoading(true);
    const validation = await validateWithXHR(message);
    if (!validation || !validation.valid) {
      setValidationError(validation?.reason || "Validation failed.");
      setLoading(false);
      return;
    }

    try {
      const payload = { message: message.trim(), user_id: (user && user.user_id) ? user.user_id : 0 };
      await axios.post(`${api}/submit`, payload);
      setMessage("");
      setValidationError("");
      if (typeof onSubmitted === "function") onSubmitted();
    } catch (err) {
      console.error(err);
      setValidationError("Submission failed — check console for details.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card">
      <form onSubmit={handleSubmit}>
        <div className="form-row">
          <input
            className="input"
            placeholder="Ask a question for the panel..."
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            aria-label="Question"
            maxLength={500}
          />
          <button className="button" type="submit" disabled={loading}>
            {loading ? "Posting..." : "Ask"}
          </button>
        </div>

        {validationError && (
          <div style={{ color: "#ff8a80", marginTop: 6, fontWeight: 700 }}>{validationError}</div>
        )}

        <div style={{ fontSize: 12, color: "var(--muted)", marginTop: 8 }}>
          Tip: Keep questions short and precise. Escalation moves items to top.
        </div>
      </form>
    </div>
  );
}
