import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { useRouter } from "next/router";
import QuestionForm from "../components/QuestionForm";
import QuestionList from "../components/QuestionList";
import WebSocketClient from "../components/WebSocket";
import { toast } from "react-toastify";

axios.defaults.baseURL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export default function Home() {
  const [questions, setQuestions] = useState([]);
  const [user, setUser] = useState(null);
  const router = useRouter();

  const [searchText, setSearchText] = useState("");
  const [searchUser, setSearchUser] = useState("");
  const [searchStatus, setSearchStatus] = useState(""); 

  useEffect(() => {
    const loggedInUser = JSON.parse(localStorage.getItem("user"));
    if (loggedInUser) setUser(loggedInUser);
    fetchQuestions(); 
  }, []);

  const fetchQuestions = useCallback(async (opts = {}) => {
    try {
      let userParam = opts.user ?? searchUser ?? undefined;
      if (typeof userParam === "string" && userParam.trim().length > 0) {
        const up = userParam.trim();
        if (up.toLowerCase() === "guest") {
          userParam = "0";
        }
      }

      const params = {
        q: opts.q ?? searchText ?? undefined,
        user: userParam ?? undefined,
        status: opts.status ?? searchStatus ?? undefined,
      };
      
      Object.keys(params).forEach((k) => {
        if (params[k] === undefined || params[k] === null || params[k] === "") delete params[k];
      });

      const res = await axios.get("/questions", { params });
      setQuestions(res.data || []);
    } catch (e) {
      console.error("Failed to fetch questions", e);
      toast.error("Failed to fetch questions");
    }
  }, [searchText, searchUser, searchStatus]);

  const handleWS = (event, payload) => {
    if (!payload) {
      fetchQuestions();
      return;
    }
    let questionId = payload?.question_id ? payload.question_id : "";
    if (event === "new_question") {
      toast.info("New question received", { autoClose: 2500 });
    } else if (event === "answered") {
      toast.success("Question " + questionId + " answered", { autoClose: 2500 });
    } else if (event === "escalated") {
      toast.warn("Question " + questionId + " escalated", { autoClose: 2500 });
    } else if (event === "new_answer") {
      toast.info("New answer received for question " + questionId, { autoClose: 2500 });
    } else if (event === "status") {
      // small info toast optional
    }
    fetchQuestions();
  };

  const handleLogout = () => {
    localStorage.removeItem("user");
    setUser(null);
    router.push("/login");
  };

  const onSearchSubmit = (e) => {
    e && e.preventDefault && e.preventDefault();
    fetchQuestions(); 
  };

  const onClearSearch =  () => {
    setSearchText("");
    setSearchUser("");
    setSearchStatus("");
    fetchQuestions({ q: "", user: "", status: "" });
    console.log('clicked clear search');
  };

  return (
    <div className="container">
      <div className="header">
        <div className="brand">
          <div className="logo">Q</div>
          <div>
            <div className="title">Q&A Dashboard</div>
            <div style={{ fontSize: 12, color: "var(--muted)" }}>Live Q&A</div>
          </div>
        </div>
        <div className="controls">
          {!user ? (
            <>
              <a href="/login" className="button secondary">Login</a>
              <a href="/register" className="button secondary">Register</a>
            </>
          ) : (
            <>
              <div>Welcome, {user.username}!</div>
              <button onClick={handleLogout} className="button secondary">Logout</button>
            </>
          )}
        </div>
      </div>

      <div className="card" style={{ marginBottom: 16 }}>
        <form onSubmit={onSearchSubmit} className="form" style={{ flexDirection: "row", alignItems: "center", gap: 8 }}>
          <input
            style={{ flex: 1 }}
            placeholder="Search text..."
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
          />
          <input
            style={{ width: 180 }}
            placeholder="User (username or id)"
            value={searchUser}
            onChange={(e) => setSearchUser(e.target.value)}
          />
          <select style={{ width: 150 }} value={searchStatus} onChange={(e) => setSearchStatus(e.target.value)}>
            <option value="">All status</option>
            <option value="Pending">Pending</option>
            <option value="Escalated">Escalated</option>
            <option value="Answered">Answered</option>
          </select>
          <button className="button" type="submit">Search</button>
          <button className="button secondary" type="button" onClick={onClearSearch}>Clear</button>
        </form>
      </div>

      <div className="grid">
        <div>
          <QuestionForm onSubmitted={() => fetchQuestions()} user={user} />
        </div>

        <div>
          <QuestionList questions={questions} user={user} onAction={() => fetchQuestions()} />
        </div>
      </div>

      <WebSocketClient onEvent={handleWS} />
    </div>
  );
}
