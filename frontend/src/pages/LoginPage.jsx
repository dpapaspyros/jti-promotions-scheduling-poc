import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import JtiLogo from "../components/JtiLogo";
import { colors } from "../theme";

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await fetch("/api/auth/login/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.error || "Login failed.");
        return;
      }
      login({ username: data.username }, data.access, data.refresh);
      navigate("/", { replace: true });
    } catch {
      setError("Unable to reach the server.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={styles.page}>
      <div style={styles.card}>
        <div style={styles.logoWrapper}>
          <JtiLogo size={44} />
        </div>

        <p style={styles.subtitle}>Promotion Scheduling</p>

        <form onSubmit={handleSubmit} style={styles.form} noValidate>
          {error && <div style={styles.error}>{error}</div>}

          <div style={styles.field}>
            <label style={styles.label} htmlFor="username">Username</label>
            <input
              id="username"
              type="text"
              autoComplete="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              style={styles.input}
              placeholder="Enter your username"
              required
            />
          </div>

          <div style={styles.field}>
            <label style={styles.label} htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              style={styles.input}
              placeholder="Enter your password"
              required
            />
          </div>

          <button type="submit" style={styles.button} disabled={loading}>
            {loading ? "Signing in…" : "Sign in"}
          </button>
        </form>
      </div>
    </div>
  );
}

const styles = {
  page: {
    minHeight: "100vh",
    backgroundColor: colors.bgPage,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    padding: "1rem",
  },
  card: {
    backgroundColor: colors.bgCard,
    border: `1px solid ${colors.border}`,
    borderRadius: "12px",
    padding: "2.5rem 2rem",
    width: "100%",
    maxWidth: "400px",
  },
  logoWrapper: {
    display: "flex",
    justifyContent: "center",
    marginBottom: "0.75rem",
  },
  subtitle: {
    textAlign: "center",
    color: colors.textMuted,
    fontSize: "0.875rem",
    letterSpacing: "0.08em",
    textTransform: "uppercase",
    marginBottom: "2rem",
  },
  form: {
    display: "flex",
    flexDirection: "column",
    gap: "1.25rem",
  },
  field: {
    display: "flex",
    flexDirection: "column",
    gap: "0.4rem",
  },
  label: {
    fontSize: "0.8rem",
    color: colors.textMuted,
    letterSpacing: "0.04em",
    textTransform: "uppercase",
  },
  input: {
    backgroundColor: colors.bgInput,
    border: `1px solid ${colors.border}`,
    borderRadius: "6px",
    color: colors.text,
    fontSize: "0.95rem",
    padding: "0.65rem 0.85rem",
    outline: "none",
    width: "100%",
    transition: "border-color 0.15s",
  },
  error: {
    backgroundColor: colors.errorBg,
    border: `1px solid ${colors.error}`,
    borderRadius: "6px",
    color: colors.error,
    fontSize: "0.85rem",
    padding: "0.6rem 0.85rem",
  },
  button: {
    marginTop: "0.5rem",
    backgroundColor: colors.buttonBg,
    color: colors.buttonText,
    border: "none",
    borderRadius: "6px",
    cursor: "pointer",
    fontSize: "0.95rem",
    fontWeight: "500",
    padding: "0.75rem",
    transition: "background-color 0.15s",
    width: "100%",
  },
};
