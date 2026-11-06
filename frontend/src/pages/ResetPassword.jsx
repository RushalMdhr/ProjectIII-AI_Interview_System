import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { confirmPasswordReset } from "../services/api";

export default function ResetPassword() {
  const { uid, token } = useParams();
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");
    setMessage("");

    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setLoading(true);
    try {
      const response = await confirmPasswordReset(uid, token, password);
      setMessage(response.message);
    } catch (requestError) {
      setError(
        requestError.response?.data?.message ||
          "This reset link is invalid or has expired. Request a new one.",
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <main style={{ minHeight: "80vh", display: "grid", placeItems: "center", padding: 24, background: "#2B2F63", color: "#FBFAFF" }}>
      <section style={{ width: "100%", maxWidth: 440, padding: 32, border: "1px solid rgba(255,255,255,.16)", borderRadius: 20, background: "rgba(255,255,255,.06)" }}>
        <h1>Set a new password</h1>
        {message ? (
          <>
            <p>{message}</p>
            <Link to="/login" style={{ color: "#45E0D0" }}>Return to login</Link>
          </>
        ) : (
          <form onSubmit={handleSubmit} style={{ display: "grid", gap: 14 }}>
            <label>
              New password
              <input
                type="password"
                autoComplete="new-password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                required
                minLength={8}
                style={{ display: "block", width: "100%", marginTop: 6, padding: 12, borderRadius: 8 }}
              />
            </label>
            <label>
              Confirm new password
              <input
                type="password"
                autoComplete="new-password"
                value={confirmPassword}
                onChange={(event) => setConfirmPassword(event.target.value)}
                required
                minLength={8}
                style={{ display: "block", width: "100%", marginTop: 6, padding: 12, borderRadius: 8 }}
              />
            </label>
            {error && <p role="alert" style={{ color: "#ffaaa5" }}>{error}</p>}
            <button type="submit" disabled={loading} style={{ padding: 12, border: 0, borderRadius: 8, cursor: "pointer" }}>
              {loading ? "Updating…" : "Update password"}
            </button>
          </form>
        )}
      </section>
    </main>
  );
}
