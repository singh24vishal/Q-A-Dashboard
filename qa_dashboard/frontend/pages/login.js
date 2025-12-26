import { useState } from "react";
import axios from "axios";
import { useRouter } from "next/router";
import Link from "next/link";

axios.defaults.baseURL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export default function Login() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const router = useRouter();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    try {
      const res = await axios.post("/login", { username, password });
      if (res.status === 200) {
        localStorage.setItem("user", JSON.stringify(res.data));
        router.push("/"); 
      }
    } catch (err) {
      setError(err?.response?.data?.detail || "Invalid credentials");
    }
  };

  return (
    <div className="container">
      <div className="auth-box card">
        <div className="auth-header">
          <h1>Login</h1>
        </div>

        <form onSubmit={handleSubmit} className="form">
          <input
            type="text"
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
            autoFocus
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />

          <button type="submit" className="button">Login</button>

          {error && <div className="error">{error}</div>}
        </form>

        <div className="auth-links">
          <div>
            <Link href="/register">Create an account</Link>
          </div>
          <div>
            <Link href="/">Back to Home</Link>
          </div>
        </div>
      </div>
    </div>
  );
}
