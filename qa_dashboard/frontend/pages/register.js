import { useState } from "react";
import { useRouter } from "next/router";
import axios from "axios";
import Link from "next/link";

axios.defaults.baseURL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export default function Register() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");  

    const passwordRegex = /^(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*]).{8,}$/;
    if (!password.match(passwordRegex)) {
      setError("Password: 8+ chars, one uppercase, one number, one special char.");
      return;
    }
    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    try {
      const res = await axios.post("/register", { username, email, password });
      if (res.status === 200) {
        localStorage.setItem("user", JSON.stringify(res.data));
        router.push("/"); 
      }
    } catch (err) {
      setError(err?.response?.data?.detail || "Registration failed.");
    }
  };

  return (
    <div className="container">
      <div className="auth-box card">
        <div className="auth-header">
          <h1>Create account</h1>
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
            type="email"
            placeholder="Email address"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          <input
            type="password"
            placeholder="Confirm password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
          />

          <button type="submit" className="button">Register</button>

          {error && <div className="error">{error}</div>}
        </form>

        <div className="auth-links">
          <div>
            <Link href="/login">Already have an account?</Link>
          </div>
          <div>
            <Link href="/">Back to Home</Link>
          </div>
        </div>
      </div>
    </div>
  );
}
