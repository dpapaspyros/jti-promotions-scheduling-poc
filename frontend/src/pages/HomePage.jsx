import { useEffect, useState } from "react";
import { useAuth, authHeaders } from "../context/AuthContext";
import JtiLogo from "../components/JtiLogo";
import { colors } from "../theme";

export default function HomePage() {
  const { user, logout } = useAuth();
  const [message, setMessage] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch("/api/hello/", { headers: authHeaders() })
      .then((res) => {
        if (res.status === 401) {
          logout();
          return;
        }
        if (!res.ok) throw new Error("API error");
        return res.json();
      })
      .then((data) => data && setMessage(data.message))
      .catch(() => setError("Could not load data from API."));
  }, [logout]);

  return (
    <div style={styles.page}>
      <nav style={styles.navbar}>
        <JtiLogo size={32} />
        <div style={styles.navRight}>
          <span style={styles.navUser}>{user?.username}</span>
          <button onClick={logout} style={styles.logoutBtn}>
            Sign out
          </button>
        </div>
      </nav>

      <main style={styles.main}>
        <h1 style={styles.heading}>Promotion Scheduling</h1>
        {message && <p style={styles.apiMessage}>{message}</p>}
        {error && <p style={styles.error}>{error}</p>}
        {!message && !error && <p style={styles.muted}>Loading…</p>}
      </main>
    </div>
  );
}

const styles = {
  page: {
    minHeight: "100vh",
    backgroundColor: colors.bgPage,
    display: "flex",
    flexDirection: "column",
  },
  navbar: {
    backgroundColor: colors.bgNavbar,
    borderBottom: `1px solid ${colors.border}`,
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: "0 2rem",
    height: "56px",
  },
  navRight: {
    display: "flex",
    alignItems: "center",
    gap: "1.25rem",
  },
  navUser: {
    color: colors.textMuted,
    fontSize: "0.875rem",
  },
  logoutBtn: {
    backgroundColor: "transparent",
    border: `1px solid ${colors.border}`,
    borderRadius: "6px",
    color: colors.text,
    cursor: "pointer",
    fontSize: "0.8rem",
    padding: "0.35rem 0.85rem",
    transition: "border-color 0.15s",
  },
  main: {
    padding: "3rem 2rem",
    maxWidth: "800px",
    width: "100%",
    margin: "0 auto",
  },
  heading: {
    fontSize: "2rem",
    fontWeight: "300",
    letterSpacing: "0.02em",
    marginBottom: "1.5rem",
  },
  apiMessage: {
    color: colors.textMuted,
    fontSize: "1rem",
  },
  muted: {
    color: colors.textMuted,
    fontSize: "1rem",
  },
  error: {
    color: colors.error,
    fontSize: "1rem",
  },
};
