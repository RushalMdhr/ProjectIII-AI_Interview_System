import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Eye, EyeOff, Sparkles } from "lucide-react";
import { login, register } from "../services/api";
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
      .rg-root * { box-sizing: border-box; }
      .rg-root { font-family: Inter, Arial, sans-serif; }
      .rg-display { font-family: "Space Grotesk", Inter, sans-serif; }
      .rg-mono { font-family: "JetBrains Mono", monospace; }

      .rg-input {
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

      .rg-input::placeholder { color: rgba(194,196,236,0.45); }

      .rg-input:focus {
        border-color: ${tokens.teal};
        background: rgba(255,255,255,0.08);
      }

      .rg-icon-btn {
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

      .rg-icon-btn:hover { color: ${tokens.text}; }
      .rg-icon-btn:focus-visible {
        outline: 2px solid ${tokens.teal};
        outline-offset: 2px;
        border-radius: 5px;
      }

      .rg-link {
        color: ${tokens.teal};
        font-weight: 600;
        text-decoration: none;
      }

      .rg-link:hover { text-decoration: underline; }

      .rg-checkbox {
        width: 16px;
        height: 16px;
        accent-color: ${tokens.teal};
        flex-shrink: 0;
      }

      .rg-primary-btn {
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

      .rg-primary-btn:hover:not(:disabled) {
        transform: translateY(-2px);
        box-shadow: 0 20px 40px -14px rgba(69,224,208,0.5);
      }

      .rg-primary-btn:disabled {
        opacity: 0.55;
        cursor: not-allowed;
        transform: none;
      }

      .rg-banner-error {
        font-size: 13.5px;
        color: #FF9A9A;
        background: rgba(255,90,90,0.10);
        border: 1px solid rgba(255,90,90,0.30);
        border-radius: 10px;
        padding: 11px 14px;
      }

      .rg-banner-success {
        font-size: 13.5px;
        color: ${tokens.teal};
        background: ${tokens.tealSoft};
        border: 1px solid ${tokens.tealLine};
        border-radius: 10px;
        padding: 11px 14px;
      }

      @media (max-width: 1024px) {
        .rg-left { display: none !important; }
      }

      @media (max-width: 520px) {
        .rg-card { padding: 32px 24px !important; }
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
        className="rg-display"
        style={{ fontSize: 17, fontWeight: 700, color: tokens.text, letterSpacing: "-0.02em" }}
      >
        AI HELPER
      </span>
    </Link>
  );
}

/* =========================================
   REGISTER
========================================= */

function Register() {
  const navigate = useNavigate();

  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const [form, setForm] = useState({
    name: "",
    email: "",
    password: "",
    confirmPassword: "",
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  const handleChange = (e) => {
    setForm((prev) => ({
      ...prev,
      [e.target.name]: e.target.value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    setError(null);
    setSuccess(null);

    if (form.password !== form.confirmPassword) {
      setError("Passwords don't match.");
      return;
    }

    if (form.password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }

    setLoading(true);

    try {
      const res = await register(form.name, form.email, form.password);

      console.log("Register response:", res);

      if (!res.success) {
        setError(res.message);
        return;
      }

      const auth = await login(form.email, form.password);

      if (!auth.success || !auth.access || !auth.refresh) {
        setError("Account created, but automatic login failed. Please log in.");
        return;
      }

      localStorage.setItem("accessToken", auth.access);
      localStorage.setItem("refreshToken", auth.refresh);
      localStorage.setItem("currentUser", JSON.stringify(auth.user));

      setSuccess(res.message);

      setTimeout(() => {
        navigate("/");
      }, 1000);

    } catch (err) {
      console.error("Registration error:", err);

      setError(
        err.response?.data?.detail ||
        err.response?.data?.message ||
        "Couldn't create your account. Try again."
      );

    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="rg-root" style={{ minHeight: "100vh", position: "relative", background: tokens.bg, color: tokens.text }}>

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

            <div
              className="rg-card"
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

              <h2 className="rg-display" style={{ fontSize: 26, fontWeight: 700, margin: "0 0 8px", color: tokens.text }}>
                Create your account
              </h2>

              <p style={{ fontSize: 14, color: tokens.textMuted, lineHeight: 1.6, margin: "0 0 28px" }}>
                Start your journey toward interview success.
              </p>

              <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 16 }}>

                {error && <div className="rg-banner-error">{error}</div>}
                {success && <div className="rg-banner-success">{success}</div>}

                <div>
                  <label style={{ display: "block", fontSize: 13, fontWeight: 600, color: tokens.textMuted, marginBottom: 8 }}>
                    Full Name
                  </label>
                  <input
                    type="text"
                    name="name"
                    value={form.name}
                    onChange={handleChange}
                    placeholder="Enter your full name"
                    required
                    className="rg-input"
                  />
                </div>

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
                    className="rg-input"
                  />
                </div>

                <div>
                  <label style={{ display: "block", fontSize: 13, fontWeight: 600, color: tokens.textMuted, marginBottom: 8 }}>
                    Password
                  </label>
                  <div style={{ position: "relative" }}>
                    <input
                      type={showPassword ? "text" : "password"}
                      name="password"
                      value={form.password}
                      onChange={handleChange}
                      placeholder="Create a password"
                      required
                      className="rg-input"
                      style={{ paddingRight: 46 }}
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="rg-icon-btn"
                      aria-label={showPassword ? "Hide password" : "Show password"}
                      aria-pressed={showPassword}
                      style={{ position: "absolute", right: 14, top: "50%", transform: "translateY(-50%)" }}
                    >
                      {showPassword ? <EyeOff size={18} strokeWidth={1.8} /> : <Eye size={18} strokeWidth={1.8} />}
                    </button>
                  </div>
                </div>

                <div>
                  <label style={{ display: "block", fontSize: 13, fontWeight: 600, color: tokens.textMuted, marginBottom: 8 }}>
                    Confirm Password
                  </label>
                  <div style={{ position: "relative" }}>
                    <input
                      type={showConfirmPassword ? "text" : "password"}
                      name="confirmPassword"
                      value={form.confirmPassword}
                      onChange={handleChange}
                      placeholder="Confirm your password"
                      required
                      className="rg-input"
                      style={{ paddingRight: 46 }}
                    />
                    <button
                      type="button"
                      onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                      className="rg-icon-btn"
                      aria-label={showConfirmPassword ? "Hide confirm password" : "Show confirm password"}
                      aria-pressed={showConfirmPassword}
                      style={{ position: "absolute", right: 14, top: "50%", transform: "translateY(-50%)" }}
                    >
                      {showConfirmPassword ? <EyeOff size={18} strokeWidth={1.8} /> : <Eye size={18} strokeWidth={1.8} />}
                    </button>
                  </div>
                </div>

                <div style={{ display: "flex", alignItems: "flex-start", gap: 9, paddingTop: 2 }}>
                  <input type="checkbox" required className="rg-checkbox" style={{ marginTop: 3 }} />
                  <p style={{ fontSize: 13, color: tokens.textMuted, margin: 0, lineHeight: 1.5 }}>
                    I agree to the Terms of Service and Privacy Policy.
                  </p>
                </div>

                <button type="submit" disabled={loading} className="rg-primary-btn">
                  {loading ? "Creating account…" : "Create Account"}
                </button>

              </form>

              <p style={{ textAlign: "center", fontSize: 13.5, color: tokens.textMuted, marginTop: 28 }}>
                Already have an account?{" "}
                <Link to="/login" className="rg-link">Login</Link>
              </p>

            </div>

          </div>

        </div>

      </div>

    </div>
  );
}

export default Register;