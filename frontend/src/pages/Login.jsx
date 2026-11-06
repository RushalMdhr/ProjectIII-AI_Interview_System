import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { Eye, EyeOff, Sparkles } from "lucide-react";
import { login, requestPasswordReset } from "../services/api";
import HomeBackground from "../components/HomeBackground";

/* =========================================
   TOKENS — same palette as HomePage
========================================= */

const tokens = {
  bg: "#2B2F63",
  bgLo: "#232752",
  glass: "rgba(255,255,255,0.06)",
  glassHi: "rgba(255,255,255,0.10)",
  border: "rgba(255,255,255,0.14)",
  violet: "#8B7CF6",
  gold: "#FFB35B",
  goldSoft: "#FFB35B2b",
  goldLine: "#FFB35B70",
  teal: "#45E0D0",
  tealSoft: "#45E0D02b",
  tealLine: "#45E0D070",
  text: "#FBFAFF",
  textMuted: "#C2C4EC",
};

/* =========================================
   GLOBAL STYLE
========================================= */

function GlobalStyle() {
  return (
    <style>{`
      .lg-root * { box-sizing: border-box; }
      .lg-root { font-family: Inter, Arial, sans-serif; }
      .lg-display { font-family: "Space Grotesk", Inter, sans-serif; }
      .lg-mono { font-family: "JetBrains Mono", monospace; }

      .lg-input {
        width: 100%;
        padding: 13px 16px;
        border-radius: 12px;
        background: rgba(255,255,255,0.05);
        border: 1.5px solid ${tokens.border};
        color: ${tokens.text};
        font-size: 14.5px;
        font-family: Inter, Arial, sans-serif;
        outline: none;
        transition: border-color 0.2s ease, background 0.2s ease;
      }

      .lg-input::placeholder { color: rgba(194,196,236,0.45); }

      .lg-input:focus {
        border-color: ${tokens.teal};
        background: rgba(255,255,255,0.08);
      }

      .lg-icon-btn {
        display: grid;
        place-items: center;
        width: 30px;
        height: 30px;
        background: none;
        border: none;
        cursor: pointer;
        color: ${tokens.textMuted};
        padding: 0;
      }

      .lg-icon-btn:hover { color: ${tokens.text}; }
      .lg-icon-btn:focus-visible {
        outline: 2px solid ${tokens.teal};
        outline-offset: 2px;
        border-radius: 5px;
      }

      .lg-link {
        color: ${tokens.teal};
        font-weight: 600;
        text-decoration: none;
      }

      .lg-link:hover { text-decoration: underline; }

      .lg-text-link {
        background: none;
        border: none;
        cursor: pointer;
        color: ${tokens.teal};
        font-size: 13px;
        font-weight: 600;
        padding: 0;
      }

      .lg-text-link:hover { text-decoration: underline; }

      .lg-checkbox {
        width: 16px;
        height: 16px;
        accent-color: ${tokens.teal};
        flex-shrink: 0;
      }

      .lg-primary-btn {
        width: 100%;
        padding: 14px;
        border-radius: 12px;
        border: none;
        cursor: pointer;
        font-family: Inter, Arial, sans-serif;
        font-size: 15px;
        font-weight: 700;
        color: ${tokens.bg};
        background: linear-gradient(100deg, ${tokens.teal}, ${tokens.gold});
        transition: transform 0.2s ease, box-shadow 0.2s ease, opacity 0.2s ease;
        box-shadow: 0 16px 32px -14px rgba(69,224,208,0.35);
      }

      .lg-primary-btn:hover:not(:disabled) {
        transform: translateY(-2px);
        box-shadow: 0 20px 40px -14px rgba(69,224,208,0.5);
      }

      .lg-primary-btn:disabled {
        opacity: 0.55;
        cursor: not-allowed;
        transform: none;
      }

      .lg-secondary-btn {
        width: 100%;
        padding: 13px;
        border-radius: 12px;
        border: 1.5px solid ${tokens.border};
        background: rgba(255,255,255,0.04);
        color: ${tokens.text};
        font-family: Inter, Arial, sans-serif;
        font-size: 14.5px;
        font-weight: 600;
        cursor: pointer;
        transition: background 0.2s ease, border-color 0.2s ease;
      }

      .lg-secondary-btn:hover {
        background: rgba(255,255,255,0.08);
        border-color: ${tokens.tealLine};
      }

      .lg-banner-error {
        font-size: 13.5px;
        color: #FF9A9A;
        background: rgba(255,90,90,0.10);
        border: 1px solid rgba(255,90,90,0.30);
        border-radius: 10px;
        padding: 11px 14px;
      }

      @media (max-width: 1024px) {
        .lg-left { display: none !important; }
      }

      @media (max-width: 520px) {
        .lg-card { padding: 32px 24px !important; }
      }
    `}</style>
  );
}

/* =========================================
   LOGO
========================================= */

function Logo() {
  return (
    <Link
      to="/"
      style={{ display: "flex", alignItems: "center", gap: 10, textDecoration: "none" }}
    >
      <div
        style={{
          width: 32,
          height: 32,
          borderRadius: 10,
          background: `linear-gradient(135deg, ${tokens.violet}, ${tokens.teal})`,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          boxShadow: `0 8px 24px rgba(69,224,208,0.18)`,
        }}
      >
        <Sparkles size={17} color={tokens.text} />
      </div>

      <span
        className="lg-display"
        style={{ fontSize: 17, fontWeight: 700, color: tokens.text, letterSpacing: "-0.02em" }}
      >
        AI HELPER
      </span>
    </Link>
  );
}

/* =========================================
   LOGIN
========================================= */

function Login() {

  const navigate = useNavigate();
  const location = useLocation();
  const [showPassword, setShowPassword] = useState(false);
  const [isResettingPassword, setIsResettingPassword] = useState(false);
  const [resetMessage, setResetMessage] = useState("");

  const [form, setForm] = useState({
    email: "",
    password: "",
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleChange = (e) => {
    setForm((prev) => ({
      ...prev,
      [e.target.name]: e.target.value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    setError(null);
    setLoading(true);

    try {
      const res = await login(form.email, form.password);

      console.log("Login response:", res);

      if (!res.success) {
        setError(res.message || "Invalid email or password.");
        return;
      }

      console.log("Logged in user:", res.user);

      if (res.access) {
        localStorage.setItem("accessToken", res.access);
      }

      if (res.refresh) {
        localStorage.setItem("refreshToken", res.refresh);
      }

      localStorage.setItem("currentUser", JSON.stringify(res.user));

      navigate(location.state?.from || "/");

    } catch (err) {
      console.error("Login error:", err);

      if (err.response?.data?.detail || err.response?.data?.message) {
        setError(err.response.data.detail || err.response.data.message);
      } else {
        setError("Couldn't log in. Check your email and password.");
      }

    } finally {
      setLoading(false);
    }
  };

  const handlePasswordResetRequest = async (e) => {
    e.preventDefault();
    setError(null);
    setResetMessage("");
    setLoading(true);

    try {
      const response = await requestPasswordReset(form.email);
      setResetMessage(response.message);
    } catch (err) {
      setError(
        err.response?.data?.message ||
          "Could not send the reset email. Please try again.",
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="lg-root" style={{ minHeight: "100vh", position: "relative", background: tokens.bg, color: tokens.text }}>

      <GlobalStyle />
      <HomeBackground tokens={tokens} />

      <div
        style={{
          position: "relative",
          zIndex: 1,
          minHeight: "100vh",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          padding: "40px 24px",
        }}
      >

        <div
          style={{
            width: "100%",
            maxWidth: 520,
            display: "grid",
            gridTemplateColumns: "1fr",
            alignItems: "center",
          }}
        >
          <div>

            <div className="lg-left" style={{ display: "none", marginBottom: 20 }}>
              {/* placeholder to keep grid balance on mobile if needed */}
            </div>

            <div
              className="lg-card"
              style={{
                background: tokens.glass,
                backdropFilter: "blur(18px)",
                WebkitBackdropFilter: "blur(18px)",
                border: `1.5px solid ${tokens.border}`,
                borderRadius: 26,
                padding: "40px 40px 36px",
                boxShadow: "0 30px 60px -30px rgba(0,0,0,0.6), inset 0 1px 0 rgba(255,255,255,0.08)",
              }}
            >

              <h2 className="lg-display" style={{ fontSize: 26, fontWeight: 700, margin: "0 0 8px", color: tokens.text }}>
                Welcome back
              </h2>

              <p style={{ fontSize: 14, color: tokens.textMuted, lineHeight: 1.6, margin: "0 0 28px" }}>
                {isResettingPassword
                  ? "Enter your email and we’ll send you a password reset link."
                  : "Sign in to continue your interview preparation."}
              </p>

              <form
                onSubmit={isResettingPassword ? handlePasswordResetRequest : handleSubmit}
                style={{ display: "flex", flexDirection: "column", gap: 18 }}
              >

                {error && <div className="lg-banner-error">{error}</div>}
                {resetMessage && (
                  <div
                    role="status"
                    style={{
                      padding: "12px 14px",
                      borderRadius: 10,
                      background: "rgba(69,224,208,0.12)",
                      color: tokens.teal,
                      fontSize: 13,
                    }}
                  >
                    {resetMessage}
                  </div>
                )}

                <div>
                  <label style={{ display: "block", fontSize: 13, fontWeight: 600, color: tokens.textMuted, marginBottom: 8 }}>
                    Email Address
                  </label>
                  <input
                    type="email"
                    name="email"
                    value={form.email}
                    onChange={handleChange}
                    placeholder="you@example.com"
                    required
                    className="lg-input"
                  />
                </div>

                {!isResettingPassword && <div>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                    <label style={{ fontSize: 13, fontWeight: 600, color: tokens.textMuted }}>
                      Password
                    </label>
                    <button
                      type="button"
                      className="lg-text-link"
                      onClick={() => {
                        setIsResettingPassword(true);
                        setError(null);
                        setResetMessage("");
                      }}
                    >
                      Forgot password?
                    </button>
                  </div>

                  <div style={{ position: "relative" }}>
                    <input
                      type={showPassword ? "text" : "password"}
                      name="password"
                      value={form.password}
                      onChange={handleChange}
                      placeholder="Enter your password"
                      required
                      className="lg-input"
                      style={{ paddingRight: 46 }}
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="lg-icon-btn"
                      aria-label={showPassword ? "Hide password" : "Show password"}
                      aria-pressed={showPassword}
                      style={{ position: "absolute", right: 14, top: "50%", transform: "translateY(-50%)" }}
                    >
                      {showPassword ? <EyeOff size={18} strokeWidth={1.8} /> : <Eye size={18} strokeWidth={1.8} />}
                    </button>
                  </div>
                </div>}

                {!isResettingPassword && <div style={{ display: "flex", alignItems: "center", gap: 9 }}>
                  <input type="checkbox" className="lg-checkbox" />
                  <span style={{ fontSize: 13.5, color: tokens.textMuted }}>Remember me</span>
                </div>}

                <button type="submit" disabled={loading} className="lg-primary-btn">
                  {loading
                    ? isResettingPassword ? "Sending…" : "Logging in…"
                    : isResettingPassword ? "Send reset link" : "Login"}
                </button>

              </form>

              {isResettingPassword && (
                <button
                  type="button"
                  className="lg-text-link"
                  onClick={() => {
                    setIsResettingPassword(false);
                    setError(null);
                    setResetMessage("");
                  }}
                  style={{ marginTop: 16 }}
                >
                  Back to login
                </button>
              )}

              {!isResettingPassword && <>
              <div style={{ display: "flex", alignItems: "center", gap: 14, margin: "26px 0" }}>
                <div style={{ height: 1, flex: 1, background: tokens.border }} />
                <span className="lg-mono" style={{ fontSize: 11, color: tokens.textMuted }}>OR</span>
                <div style={{ height: 1, flex: 1, background: tokens.border }} />
              </div>

              <button
                type="button"
                onClick={() => {
                  window.location.href = "http://localhost:8000/accounts/google/login/";
                }}
                className="lg-secondary-btn"
              >
                Continue with Google
              </button>

              <p style={{ textAlign: "center", fontSize: 13.5, color: tokens.textMuted, marginTop: 28 }}>
                Don't have an account?{" "}
                <Link to="/register" className="lg-link">Create account</Link>
              </p>
              </>}

            </div>

          </div>

        </div>

      </div>

    </div>
  );
}

export default Login;