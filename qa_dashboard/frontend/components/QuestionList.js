import dayjs from "dayjs";
import axios from "axios";
import classNames from "classnames";
import { toast } from "react-toastify";
import { useState } from "react";

export default function QuestionList({ questions, user, onAction }) {
  const api = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

  const markAnswered = async (id) => {
    if (!user) { toast.warn("You must log in to mark answered"); return; }
    try {
      await axios.post(`${api}/mark_answered?question_id=${id}`);
      if (onAction) onAction();
    } catch (e) {
      console.error(e);
      toast.error("Failed to mark answered");
    }
  };

  const escalate = async (id) => {
    if (!user) { toast.warn("You must log in to escalate"); return; }
    try {
      await axios.post(`${api}/escalate?question_id=${id}`);
      if (onAction) onAction();
    } catch (e) {
      console.error(e);
      toast.error("Failed to escalate");
    }
  };

  const copyText = async (text) => {
    try {
      await navigator.clipboard.writeText(text);
      toast.success("Copied to clipboard");
    } catch (err) {
      try {
        const ta = document.createElement("textarea");
        ta.value = text;
        ta.style.position = "fixed";
        ta.style.left = "-9999px";
        document.body.appendChild(ta);
        ta.select();
        document.execCommand("copy");
        document.body.removeChild(ta);
        toast.success("Copied to clipboard");
      } catch (e) {
        console.error("Clipboard failed", e);
        toast.error("Copy failed");
      }
    }
  };

  const [openAnswersFor, setOpenAnswersFor] = useState(null);

  const submitAnswer = async (question_id) => {
    const ans = prompt("Type your answer:");
    if (!ans || !ans.trim()) return;
    const payload = {
      question_id,
      user_id: user && user.user_id ? user.user_id : 0,
      message: ans.trim(),
    };
    try {
      const res = await axios.post(`${api}/answer`, payload);
      toast.success("Answer posted");
      if (onAction) onAction();
      setOpenAnswersFor(question_id);
    } catch (e) {
      console.error("Failed to post answer", e);
      toast.error("Failed to post answer");
    }
  };

  return (
    <div className="card">
      <div style={{ marginBottom: 10, fontWeight: 800 }}>Live Questions</div>
      <div className="q-list">
        {questions.length === 0 && <div style={{ color: "var(--muted)" }}>No questions yet.</div>}
        {questions.map((q) => (
          <div key={q.question_id} className="q-item" style={{ flexDirection: "column", alignItems: "stretch" }}>
            <div style={{ display: "flex", justifyContent: "space-between", gap: 12 }}>
              <div className="q-left">
                <div className="avatar">{String(q.question_id).slice(-2)}</div>
                <div>
                  <div className="q-meta">
                    <span style={{ marginRight: 8 }}>
                      {q.user_id && q.user_id !== 0 ? (q.username ? q.username : `User ${q.user_id}`) : "Guest"}
                    </span>
                    <span className="q-time">{dayjs(q.timestamp).format("MMM D, HH:mm:ss")}</span>
                  </div>
                  <div className="q-message">{q.message}</div>
                </div>
              </div>

              <div style={{ textAlign: "right" }}>
                <div style={{ marginBottom: 8 }}>
                  <span
                    className={classNames("badge", {
                      pending: q.status === "Pending",
                      escalated: q.status === "Escalated",
                      answered: q.status === "Answered",
                    })}
                  >
                    {q.status}
                  </span>
                </div>

                <div className="actions">
                  <button type="button" className="small ghost" onClick={() => copyText(q.message)}>
                    Copy
                  </button>

                  <button type="button" className="small" onClick={() => submitAnswer(q.question_id)}>
                    Answer
                  </button>

                  <button type="button" className="small warn" onClick={() => escalate(q.question_id)}>Escalate</button>
                  <button type="button" className="small positive" onClick={() => markAnswered(q.question_id)}>Mark Answered</button>
                </div>
              </div>
            </div>

            <div style={{ marginTop: 10 }}>
              <div style={{ display: "flex", justifyContent: "flex-end" }}>
                <button
                  className="small ghost"
                  onClick={() => setOpenAnswersFor(openAnswersFor === q.question_id ? null : q.question_id)}
                >
                  {`Answers (${(q.answers && q.answers.length) || 0}) ${openAnswersFor === q.question_id ? "▲" : "▼"}`}
                </button>
              </div>

              {openAnswersFor === q.question_id && (
                <div style={{ marginTop: 10, padding: 10, borderRadius: 8, background: "rgba(255,255,255,0.02)" }}>
                  {(!q.answers || q.answers.length === 0) && <div style={{ color: "var(--muted)" }}>No answers yet.</div>}
                  {(q.answers || []).map((a) => (
                    <div key={a.answer_id} style={{ marginBottom: 8, borderBottom: "1px solid rgba(255,255,255,0.02)", paddingBottom: 8 }}>
                      <div style={{ fontSize: 13, color: "var(--muted)", marginBottom: 4 }}>
                        <strong style={{ color: "#e6eef6" }}>{a.username || (a.user_id && a.user_id !== 0 ? `User ${a.user_id}` : "Guest")}</strong>
                        {" · "}
                        <span>{dayjs(a.timestamp).format("MMM D, HH:mm:ss")}</span>
                      </div>
                      <div style={{ color: "#e6eef6" }}>{a.message}</div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
